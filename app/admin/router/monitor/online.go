package monitor

import (
	"github.com/gin-gonic/gin"
	"github.com/x-thooh/thooh-admin/app/admin/api/monitor"
	"github.com/x-thooh/thooh-admin/app/core/utils/jwt"
)

func InitOnLine(e *gin.Engine) {
	// 在线用户相关
	v := e.Group("monitor/online")
	{
		auth := v.Group("")
		auth.Use(jwt.JWTAuthMiddleware())
		{
			auth.GET("list", monitor.ListOnLine)
			auth.DELETE("/:tokenId", monitor.DetectOnLine)
		}
	}
}
