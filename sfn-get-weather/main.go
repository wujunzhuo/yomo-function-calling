package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"time"

	"github.com/yomorun/yomo"
	"github.com/yomorun/yomo/serverless"

	"demo"
)

type Msg struct {
	CityName string `json:"city_name"`
}

func Handler(ctx serverless.Context) {
	var msg Msg
	err := json.Unmarshal(ctx.Data(), &msg)
	if err != nil {
		ctx.Write(0x30, []byte("error: json unmarshal error: "+err.Error()))
		return
	}

	// mock weather
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	temprature := r.Intn(30)

	res := fmt.Sprintf("ok: current temperature of %s is %d°C", msg.CityName, temprature)
	ctx.Write(0x30, []byte(res))
}

func main() {
	sfn := yomo.NewStreamFunction("get-weather", demo.ZipperAddr)
	sfn.SetObserveDataTags(0x32)
	sfn.SetHandler(Handler)
	err := sfn.Connect()
	if err != nil {
		log.Fatalln(err)
	}
	defer sfn.Close()
	sfn.Wait()
}
