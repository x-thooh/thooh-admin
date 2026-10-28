package system

import (
	"github.com/gin-gonic/gin"
	"github.com/x-thooh/thooh-admin/app/admin/api/system"
	"github.com/x-thooh/thooh-admin/app/core/utils/jwt"
)

func InitNotice(e *gin.Engine) {
	// 消息相关
	v := e.Group("system/notice")
	{
		auth := v.Group("")
		auth.Use(jwt.JWTAuthMiddleware())
		{
			auth.GET("/list", system.ListNotice)
			auth.GET("/:noticeId", system.GetNotice)
			auth.POST("", system.SaveNotice)
			auth.PUT("", system.UploadNotice)
			auth.DELETE("/:noticeIds", system.DeleteNotice)
		}
	}
}
