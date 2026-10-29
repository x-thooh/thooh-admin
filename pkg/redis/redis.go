package redis

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/x-thooh/thooh-admin/common/config"

	"github.com/go-redis/redis/v8"
)

type connect struct {
	client *redis.Client
}

var once = sync.Once{}

var _connect *connect

func connectRedis() error {
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	addr := config.Redis.Host + ":" + config.Redis.Port
	c := redis.NewClient(&redis.Options{
		Addr: addr,
		DB:   config.Redis.DB,
		// 密码只进连接，不进错误消息：这行会进容器 stdout。
		Password: config.Redis.Password,
	})

	if err := c.Ping(ctx).Err(); err != nil {
		return fmt.Errorf("redis %s 连不上：%w", addr, err)
	}

	_connect = &connect{
		client: c,
	}
	return nil
}

func Client() *redis.Client {
	if _connect == nil {
		once.Do(func() {
			if err := connectRedis(); err != nil {
				// 同 mysql：panic 会被 Recovery 咽成 500，这里要的是带地址的一条人话
				log.Fatalf("启动失败：%v", err)
			}
		})
	}
	return _connect.client
}
