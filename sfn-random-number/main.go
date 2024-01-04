package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"

	"github.com/yomorun/yomo"
	"github.com/yomorun/yomo/serverless"

	"demo"
)

type Msg struct {
	Seed  int   `json:"seed"`
	Range []int `json:"range"`
}

func Handler(ctx serverless.Context) {
	var msg Msg
	err := json.Unmarshal(ctx.Data(), &msg)
	if err != nil {
		ctx.Write(0x41, []byte("json unmarshal error: "+err.Error()))
		return
	}

	if len(msg.Range) != 2 {
		ctx.Write(0x41, []byte("random range should be with two numbers"))
		return
	}

	r := rand.New(rand.NewSource(int64(msg.Seed)))
	num := r.Intn(msg.Range[1] - msg.Range[0])

	ctx.Write(0x30, []byte(fmt.Sprintf("ok: generated new number [%d]", num)))
}

func main() {
	sfn := yomo.NewStreamFunction("random-number", demo.ZipperAddr)
	sfn.SetObserveDataTags(0x31)
	sfn.SetHandler(Handler)
	err := sfn.Connect()
	if err != nil {
		log.Fatalln(err)
	}
	defer sfn.Close()
	sfn.Wait()
}
