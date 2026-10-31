package auth

import (
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/x-thooh/thooh-admin/app/admin/model/cache"
	utils2 "github.com/x-thooh/thooh-admin/app/core/utils"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/app/core/utils/jwt"
	"github.com/x-thooh/thooh-admin/common/config"
	lolog "github.com/x-thooh/thooh-admin/modules/mon/login"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	useragent "github.com/wenlng/go-user-agent"
)

func Login(c *gin.Context) {
	var bo LoginBo
	if err := c.ShouldBind(&bo); err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg("参数不能为空"))
		return
	}
	if captchaEnabled() && !utils2.VerifyCaptcha(bo.Uuid, bo.Code) {
		lolog.Insert(c, bo.UserName, "登录失败，验证码错误", false)
		c.JSON(http.StatusOK, R.ReturnFailMsg("请输入正确的验证码"))
		return
	}
	u, err := findUser(bo.UserName)
	if err != nil {
		lolog.Insert(c, bo.UserName, "登录失败，用户不存在", false)
		c.JSON(http.StatusOK, R.ReturnFailMsg("用户不存在"))
		return
	}
	count := cache.GetPasswordTryCount(bo.UserName)
	if count >= config.UserPassword.MaxRetryCount {
		lolog.Insert(c, bo.UserName, "登录失败，密码错误达到最大次数", false)
		c.JSON(http.StatusOK, R.ReturnFailMsg("登录失败次数过多，请稍后再试"))
		return
	}
	if !utils2.PasswordVerify(bo.Password, u.Password) {
		cache.SetPasswordTryCount(bo.UserName, count+1)
		lolog.Insert(c, bo.UserName, "登录失败，密码错误", false)
		c.JSON(http.StatusOK, R.ReturnFailMsg("用户名或密码错误"))
		return
	}
	cache.DeletePasswordTryCount(bo.UserName)

	newUUID, err := uuid.NewUUID()
	if err != nil {
		lolog.Insert(c, bo.UserName, "登录失败，"+err.Error(), false)
		c.JSON(http.StatusOK, R.ReturnFailMsg("登录失败"))
		return
	}
	tokenId := newUUID.String()
	tokenString, err := jwt.CreateToken(u.Username, u.Id, u.Orgid, tokenId)
	if err != nil {
		lolog.Insert(c, bo.UserName, "登录失败，"+err.Error(), false)
		c.JSON(http.StatusOK, R.ReturnFailMsg("登录失败"))
		return
	}
	userAgent := c.Request.Header.Get("User-Agent")
	err = saveSession(Session{
		TokenId:       tokenId,
		UserId:        u.Id,
		UserName:      u.Username,
		NickName:      u.Name,
		OrgId:         u.Orgid,
		OrgName:       findOrgName(u.Orgid),
		Ipaddr:        c.ClientIP(),
		LoginLocation: lolog.GetRealAddressByIP(c.ClientIP()),
		Browser:       useragent.GetBrowserName(userAgent),
		Os:            useragent.GetOsName(userAgent),
		LoginTime:     time.Now().Unix(),
	})
	if err != nil {
		log.Printf("登录失败：%v\n", err)
		lolog.Insert(c, bo.UserName, "登录失败，"+err.Error(), false)
		c.JSON(http.StatusOK, R.ReturnFailMsg("登录失败"))
		return
	}
	lolog.Insert(c, bo.UserName, "登录成功", true)
	c.JSON(http.StatusOK, gin.H{
		"msg":   "登录成功",
		"code":  http.StatusOK,
		"token": tokenString,
		"data":  LoginVo{AccessToken: tokenString, ExpireIn: int64(config.Jwt.JwtTtl)},
	})
}

// GetInfo 的响应是平铺的 user / roles / permissions：web/admin 的 GetInfo action 与
// web/mobile 的 Info store 都直接读这三个顶层键，包一层 data 两边一起白屏。
// user 里逐个字段点名取，不把手上的 SysUser 整个 Marshal 出去——口令列就在结构体里（T-31）。
func GetInfo(c *gin.Context) {
	userId := c.GetString("userId")
	u, err := findUserById(userId)
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	roles, err := roleNames(userId)
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	permissions, err := permissionCodes(userId)
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"msg":  "获取成功",
		"code": http.StatusOK,
		"user": UserVo{
			UserId:      u.Id,
			UserName:    u.Username,
			NickName:    u.Name,
			Phonenumber: u.Monum,
			Email:       u.Email,
			Avatar:      u.Avatar,
			Sex:         u.Gender,
			CreateTime:  u.Crtim,
			Dept:        findOrg(u.Orgid),
		},
		"roles":       roles,
		"permissions": permissions,
	})
}

func GetRouters(c *gin.Context) {
	granted, err := grantedMenus(c.GetString("userId"))
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"msg":  "获取成功",
		"code": http.StatusOK,
		"data": buildRouters(granted),
	})
}

func Logout(c *gin.Context) {
	jwtUuid, err := jwt.GetJwtUuid(c)
	if err == nil && len(jwtUuid) > 0 {
		dropSession(jwtUuid)
		lolog.Insert(c, c.GetString("userName"), "退出成功", true)
	}
	c.JSON(http.StatusOK, gin.H{
		"msg":  "退出成功",
		"code": http.StatusOK,
	})
}

// Code 的响应是平铺的：web/admin 读 res.data.captchaEnabled / res.data.img，
// img 还要去掉 base64 前缀——这个形状是量出来的，不是设计出来的。
func Code(c *gin.Context) {
	enabled := captchaEnabled()
	if !enabled {
		c.JSON(http.StatusOK, gin.H{
			"msg":            "操作成功",
			"code":           http.StatusOK,
			"captchaEnabled": false,
		})
		return
	}
	id, b64s, err := utils2.CreateImageCaptcha()
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg("创建验证码失败，请联系管理员"))
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"msg":            "操作成功",
		"code":           http.StatusOK,
		"captchaEnabled": true,
		"uuid":           id,
		"img":            strings.ReplaceAll(b64s, "data:image/png;base64,", ""),
	})
}
