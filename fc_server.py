from __future__ import annotations
import json
import subprocess
from fastapi import FastAPI
from pydantic import BaseModel
import chatglm_cpp
import uvicorn

MODEL_PATH = "./chatglm3-ggml.bin"
SOURCE_EXEC_PATH = "./source_exec"

SINK_TAG = 0x30

FUNCTION_TAGS = {
    "random_number_generator": 0x31,
    "get_weather": 0x32,
}


TOOLS = [
    {
        "name": "random_number_generator",
        "description": "Generates a random number x, s.t. range[0] <= x < range[1]",
        "parameters": {
            "type": "object",
            "properties": {
                "seed": {"description": "The random seed used by the generator", "type": "integer"},
                "range": {
                    "description": "The range of the generated numbers",
                    "type": "array",
                    "items": [{"type": "integer"}, {"type": "integer"}],
                },
            },
            "required": ["seed", "range"],
        },
    },
    {
        "name": "get_weather",
        "description": "Get the current weather for `city_name`",
        "parameters": {
            "type": "object",
            "properties": {"city_name": {"description": "The name of the city to be queried", "type": "string"}},
            "required": ["city_name"],
        },
    },
]

SYSTEM_PROMPT = (
    "Answer the following questions as best as you can. You have access to the following tools:\n"
    + json.dumps(TOOLS, indent=4)
)


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


def run_function(name: str, arguments: str) -> str:
    def tool_call(**kwargs):
        return json.dumps(kwargs)

    tag = FUNCTION_TAGS.get(name)
    if tag is None:
        return f"Function `{name}` is not defined"

    try:
        payload = eval(arguments, dict(tool_call=tool_call))
    except Exception:
        send_to_yomo(SINK_TAG, f"error: Invalid arguments {arguments}")

    send_to_yomo(tag, payload)


pipeline = chatglm_cpp.Pipeline(MODEL_PATH)


def run(prompt: str):
    prompt = prompt.strip()

    messages = [
        Message(role="system", content=SYSTEM_PROMPT),
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

    reply_message = Message.from_cpp(
        pipeline.merge_streaming_messages(chunks))
    if not reply_message.tool_calls:
        return

    (tool_call,) = reply_message.tool_calls
    if tool_call.type == "function":
        print('name:', tool_call.function.name)
        print('arguments:', tool_call.function.arguments)
        run_function(tool_call.function.name, tool_call.function.arguments)
    else:
        send_to_yomo(
            SINK_TAG, f"error: Unexpected tool call type {tool_call.type}")


app = FastAPI()


class Request(BaseModel):
    prompt: str


@app.post("/")
async def api(req: Request):
    run(req.prompt)
    return {"Msg": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2880)
