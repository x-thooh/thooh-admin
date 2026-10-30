package jwt

import (
	"net/http"
	"strings"

	"github.com/x-thooh/thooh-admin/app/admin/model/constants"
	config2 "github.com/x-thooh/thooh-admin/common/config"
	"github.com/x-thooh/thooh-admin/pkg/cache/redisCache"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt"
)

// publicExact 是登录前必须可达的确切路径：登录三件套与前端预检。
// /index 是 web/admin 登录前打的（实测 4 处引用），挡住它就等于白屏。
var publicExact = []string{"/", "/old", "/protocol.html", "/index", "/login", "/logout", "/captchaImage"}

// publicPrefix 是静态资源与免鉴权前缀。边界靠末尾的 "/" 或整段匹配把
// /staticx 这类误放行挡住。
var publicPrefix = []string{"/admin/", "/static/", "/profile/", "/favicon.ico", "/auth/login", "/auth/code", "/swagger/"}

func isPublic(path string) bool {
	for _, p := range publicExact {
		if path == p {
			return true
		}
	}
	for _, p := range publicPrefix {
		if strings.HasPrefix(path, p) {
			return true
		}
	}
	// /admin、/static 这两个挂载点自身（不带斜杠）也要放行，否则前端拿不到入口页
	return path == "/admin" || path == "/static" || path == "/profile" || path == "/auth/logout"
}

// isPageNavigation 认的是「浏览器地址栏刷新」这一类请求：GET + Accept: text/html +
// 没有命中任何注册路由（gin 的 FullPath() 为空），这种请求最终走 r.NoRoute 的 SPA 回落拿 index.html。
// 只看 Accept 是不够的——伪造一句 `Accept: text/html` 打已注册的 /sys/user 也算导航的话，
// 门就白装了；所以「没注册」这个条件必须一起成立。
func isPageNavigation(ctx *gin.Context) bool {
	if ctx.Request.Method != http.MethodGet {
		return false
	}
	if !strings.Contains(ctx.Request.Header.Get("Accept"), "text/html") {
		return false
	}
	return ctx.FullPath() == ""
}

// Gate 是全局鉴权门：默认要 token，公开面显式列出来。
// 反过来写（默认放开、逐个组挂鉴权）就是看板 T-27 的成因——新加一个模块自动不需要 token。
func Gate() gin.HandlerFunc {
	return func(ctx *gin.Context) {
		if isPublic(ctx.Request.URL.Path) || isPageNavigation(ctx) {
			ctx.Next()
			return
		}
		tokenStr := ctx.Request.Header.Get(config2.HeaderSignToken)
		if len(tokenStr) < 1 {
			ctx.JSON(http.StatusOK, gin.H{
				"msg":  "令牌不能为空",
				"code": http.StatusUnauthorized,
			})
			ctx.Abort()
			return
		}
		token, err := VerifyToken(tokenStr)
		if err != nil {
			ctx.JSON(http.StatusOK, gin.H{
				"msg":  "认证失败",
				"code": http.StatusUnauthorized,
			})
			ctx.Abort()
			return
		}
		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			ctx.JSON(http.StatusOK, gin.H{"msg": "认证失败", "code": http.StatusUnauthorized})
			ctx.Abort()
			return
		}
		uuid, _ := claims["uuid"].(string)
		loginUser, err := redisCache.NewRedisCache().Get(constants.LoginCacheKey + uuid)
		if len(loginUser) <= 0 || err != nil {
			ctx.JSON(http.StatusOK, gin.H{
				"msg":  "认证失败",
				"code": http.StatusUnauthorized,
			})
			ctx.Abort()
			return
		}
		// 此处已经通过了, 可以把Claims中的有效信息拿出来放入上下文使用
		ctx.Set("userId", claims["user_id"])
		ctx.Set("deptId", claims["dept_id"])
		ctx.Set("userName", claims["user_name"])
		ctx.Next()
	}
}
