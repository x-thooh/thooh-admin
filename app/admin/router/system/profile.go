package system

import (
	"github.com/gin-gonic/gin"
	"github.com/x-thooh/thooh-admin/app/admin/api/system"
	"github.com/x-thooh/thooh-admin/app/core/utils/jwt"
)

func InitProfile(e *gin.Engine) {
	v := e.Group("system/user")
	{
		auth := v.Group("")
		auth.Use(jwt.JWTAuthMiddleware())
		{
			auth.PUT("profile/updatePwd", system.UpdatePwdHandler)
			auth.GET("profile", system.ProfileHandler)
			auth.PUT("profile", system.PostProfileHandler)
			auth.POST("profile/avatar", system.AvatarHandler)
		}
	}
}
