package main

import (
	"log"
	"os"
	"strconv"
	"time"

	"github.com/yomorun/yomo"

	"demo"
)

func main() {
	tag, err := strconv.Atoi(os.Args[1])
	if err != nil {
		log.Fatalln(err)
	}
	payload := os.Args[2]

	source := yomo.NewSource("source", demo.ZipperAddr)
	err = source.Connect()
	if err != nil {
		log.Fatalln(err)
	}
	defer source.Close()

	err = source.Write(uint32(tag), []byte(payload))
	if err != nil {
		log.Fatalln(err)
	}

	time.Sleep(time.Second * 1)
}
