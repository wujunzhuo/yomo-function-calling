# yomo-function-calling

## Download chatglm model Or Use Azure OpenAI Service

```sh
curl -o chatglm3-ggml.bin "https://www.modelscope.cn/api/v1/models/tiansz/chatglm3-6b-ggml/repo?Revision=master&FilePath=chatglm3-ggml.bin"
```

Or

```sh
export AZURE_OPENAI_KEY=******
```

## Install python libs

```sh
sudo apt install python3-virtualenv
virtualenv venv
source venv/bin/activate

pip install chatglm_cpp fastapi pydantic uvicorn openai
```

## Compile YoMo Source

```sh
go build -o source_exec ./source
```

## Start python server

```sh
python fc_server.py
```

## Start YoMo Zipper

```sh
yomo serve -c zipper-config.yaml
```

## Start application SFN

```sh
cd sfn-get-weather
go run main.go
```

## Start sink SFN

```sh
cd sfn-sink
go run main.go
```

## Chat as YoMo Source

```sh
curl -H "Content-type: application/json" -d '{"prompt":"北京的天气怎么样？"}' http://localhost:2880
# {"msg":"ok","tag":50,"payload":"{\"city_name\": \"\\u5317\\u4eac\"}"}

curl -H "Content-type: application/json" -d '{"prompt":"你叫什么名字？"}' http://localhost:2880
# {"msg":"error: This prompt cannot be recognized as a function"}
```
