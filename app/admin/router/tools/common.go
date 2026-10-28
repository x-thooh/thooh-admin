package tools

import (
	"github.com/gin-gonic/gin"
	"github.com/x-thooh/thooh-admin/app/admin/api/tools"
	"github.com/x-thooh/thooh-admin/app/core/utils/jwt"
)

func InitCommon(e *gin.Engine) {
	// 公共相关
	v := e.Group("common")
	{
		auth := v.Group("")
		auth.Use(jwt.JWTAuthMiddleware())
		{
			auth.GET("/download", tools.GetDownload)
			auth.POST("/upload", tools.UploadCommon)
			auth.POST("/uploads", tools.UploadCommons)
			auth.GET("/download/resource", tools.UploadRsource)
		}
	}
}
