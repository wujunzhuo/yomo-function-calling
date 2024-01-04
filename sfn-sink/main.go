package main

import (
	"fmt"
	"log"

	"github.com/yomorun/yomo"
	"github.com/yomorun/yomo/serverless"

	"demo"
)

func Handler(ctx serverless.Context) {
	fmt.Println(string(ctx.Data()))
}

func main() {
	sfn := yomo.NewStreamFunction("sink", demo.ZipperAddr)
	sfn.SetObserveDataTags(0x30)
	sfn.SetHandler(Handler)
	err := sfn.Connect()
	if err != nil {
		log.Fatalln(err)
	}
	defer sfn.Close()
	sfn.Wait()
}
