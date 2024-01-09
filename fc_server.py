from __future__ import annotations
import json
import logging
import os
import subprocess
from fastapi import FastAPI
from pydantic import BaseModel
from openai import AzureOpenAI
import chatglm_cpp
import uvicorn

CHATGLM_MODEL_PATH = "./chatglm3-ggml.bin"

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt35")
AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_VERSION", "2023-12-01-preview")

if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY:
    azure_openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_VERSION,
    )
    chatglm_pipeline = None
else:
    azure_openai_client = None
    chatglm_pipeline = chatglm_cpp.Pipeline(CHATGLM_MODEL_PATH)


FUNCTION_DESC_PATH = "./function_desc.json"
FUNCTION_TAG_PATH = "./function_tag.json"
SOURCE_EXEC_PATH = "./source_exec"

with open(FUNCTION_DESC_PATH, "r") as f:
    FUNCTION_DESC = json.load(f)

with open(FUNCTION_TAG_PATH, 'r') as f:
    FUNCTION_TAGS = json.load(f)


class Message(chatglm_cpp.ChatMessage):
    def __init__(
        self, role: str, content: str, tool_calls: list | None = None,
    ) -> None:
        if tool_calls is None:
            tool_calls = []
        super().__init__(role, content, tool_calls)

    @staticmethod
    def from_cpp(cpp_message: chatglm_cpp.ChatMessage) -> Message:
        return Message(
            role=cpp_message.role, content=cpp_message.content,
            tool_calls=cpp_message.tool_calls
        )


def send_to_yomo(tag: int, payload: str) -> None:
    subprocess.run([SOURCE_EXEC_PATH, str(tag), payload])


def parse_tag_and_payload(name: str, arguments: str) -> str:
    def tool_call(**kwargs):
        return json.dumps(kwargs)

    tag = FUNCTION_TAGS.get(name)
    if tag is None:
        raise ValueError(f"Function `{name}` is not defined")

    try:
        json.loads(arguments)
        payload = arguments
    except json.JSONDecodeError:
        payload = eval(arguments, dict(tool_call=tool_call))

    return tag, payload


def run_llm(prompt: str):
    prompt = prompt.strip()

    if azure_openai_client:
        return run_azure_openai(azure_openai_client, prompt)
    else:
        return run_chatglm_model(chatglm_pipeline, prompt)


def run_azure_openai(client: AzureOpenAI, prompt: str):
    response = client.chat.completions.create(
        model=AZURE_OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "function", "function": x} for x in FUNCTION_DESC],
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    if response_message.tool_calls:
        return response_message.tool_calls[0]


def run_chatglm_model(pipeline: chatglm_cpp.Pipeline, prompt: str):
    system_prompt = "Answer the following questions as best as you can. \
You have access to the following tools:\n" \
    + json.dumps(FUNCTION_DESC, indent=4)

    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=prompt)
    ]

    chunks = []
    response = ""

    for chunk in pipeline.chat(
        messages,
        max_length=2048,
        max_context_length=1536,
        do_sample=True,
        top_k=0,
        top_p=0.8,
        temperature=0.8,
        repetition_penalty=1.0,
        num_threads=0,
        stream=True,
    ):
        response += chunk.content
        chunks.append(chunk)

    reply_message = Message.from_cpp(pipeline.merge_streaming_messages(chunks))
    if reply_message.tool_calls:
        return reply_message.tool_calls[0]


app = FastAPI()
logger = logging.getLogger("uvicorn")


class Request(BaseModel):
    prompt: str


@app.post("/")
async def api(req: Request):
    logger.info(f"prompt: {req.prompt}")
    tool_call = run_llm(req.prompt)
    if tool_call is None:
        return {"msg": "error: This prompt cannot be recognized as a function"}

    if tool_call.type == "function":
        try:
            logger.info(f"function: {tool_call.function.name}")
            logger.info(f"arguments: {tool_call.function.arguments}")
            tag, payload = parse_tag_and_payload(
                tool_call.function.name, tool_call.function.arguments)
            send_to_yomo(tag, payload)
            return {
                "msg": "ok",
                "tag": tag,
                "payload": payload
            }
        except Exception as e:
            return {"msg": "error: " + str(e)}
    else:
        return {"msg": f"error: Unexpected tool call type {tool_call.type}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2880)
