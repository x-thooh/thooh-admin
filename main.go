package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"runtime"
	"strconv"

	"github.com/x-thooh/thooh-admin/app/admin/model/cache"
	"github.com/x-thooh/thooh-admin/app/core/routers"
	"github.com/x-thooh/thooh-admin/app/core/utils"
	"github.com/x-thooh/thooh-admin/app/core/utils/job"
	"github.com/x-thooh/thooh-admin/app/core/utils/shutdown"
	"github.com/x-thooh/thooh-admin/common/config"
	"github.com/x-thooh/thooh-admin/pkg/logs"
	"github.com/x-thooh/thooh-admin/pkg/scheduler"

	xxl_job_executor_gin "github.com/gin-middleware/xxl-job-executor"
)

var configFile = flag.String("f", "./config.yaml", "")

// @title github.com/x-thooh/thooh-admin-go 接口文档
// @version v1.0.2
// @description 基于Go，gin，JWT，vue前后端分离的权限管理系统
// @contact.name github.com/x-thooh/thooh-admin-go
// @contact.url https://gitee.com/github.com/x-thooh/thooh-admin/github.com/x-thooh/thooh-admin-go
// @host 127.0.0.1:8080
// @BasePath /
func main() {
	fmt.Println("hello github.com/x-thooh/thooh-admin-go")
	logs.Poster()
	// 初始化配置文件
	config.InitAppConfig(*configFile)
	// 初始化 定时
	scheduler.InitCron()

	// 初始化路由
	r := routers.Init()

	// xxl_job
	if config.XxlJob.Enabled {
		cron := job.InitXxlJobCron()
		xxl_job_executor_gin.XxlJobMux(r, cron)
	}
	// 初始化缓存
	cache.InitCache()
	//打开浏览器
	if runtime.GOOS == "windows" {
		utils.OpenWin("http://127.0.0.1:" + strconv.Itoa(config.Server.Port))
	}

	if runtime.GOOS == "darwin" {
		utils.OpenMac("http://127.0.0.1:" + strconv.Itoa(config.Server.Port))
	}

	srv := &http.Server{
		Addr:    ":" + strconv.Itoa(config.Server.Port),
		Handler: r,
	}

	go func() {
		// 启动服务
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("启动失败，listen: %s\n", err)
		}
	}()

	// 优雅关闭
	shutdown.GracefullyShutdown(srv)
}
