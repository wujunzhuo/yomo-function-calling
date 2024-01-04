package demo

import "os"

var (
	ZipperAddr = "localhost:2881"
)

func init() {
	if v := os.Getenv("ZIPPER_ADDR"); v != "" {
		ZipperAddr = v
	}
}
