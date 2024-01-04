# yomo-function-calling

## Download chatglm model

```sh
curl -o chatglm3-ggml.bin "https://www.modelscope.cn/api/v1/models/tiansz/chatglm3-6b-ggml/repo?Revision=master&FilePath=chatglm3-ggml.bin"
```

## Install python libs

```sh
sudo apt install python3-virtualenv
virtualenv venv
source venv/bin/activate

pip install chatglm_cpp fastapi pydantic uvicorn
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
cd sfn-random-number
go run main.go

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
```
