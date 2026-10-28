package monitor

import (
	"github.com/gin-gonic/gin"
	"github.com/x-thooh/thooh-admin/app/admin/api/monitor"
	"github.com/x-thooh/thooh-admin/app/core/utils/jwt"
)

// InitLogininfor 登录日志
func InitLogininfor(e *gin.Engine) {
	// 登录日志相关
	v := e.Group("monitor/logininfor")
	{
		auth := v.Group("")
		auth.Use(jwt.JWTAuthMiddleware())
		{
			auth.GET("/list", monitor.LoginInformListHandler)
			auth.POST("/export", monitor.ExportHandler)
			auth.DELETE("/:infoIds", monitor.DeleteByIdHandler)
			auth.DELETE("/clean", monitor.CleanHandler)
			auth.GET("/unlock/:userName", monitor.UnlockHandler)
		}
	}
}
