package jwt

import (
	"github.com/x-thooh/thooh-admin/app/admin/model/constants"
	config2 "github.com/x-thooh/thooh-admin/common/config"
	"github.com/x-thooh/thooh-admin/pkg/cache/redisCache"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt"
)

// CreateToken 的两个 id 是字符串：dump 里 sys_user.id 与 sys_org.id 都是 varchar(36)，
// claim 换成 int 会在每一棵子树上取不到用户。
func CreateToken(UserName string, UserId string, DeptId string, uuid string) (string, error) {
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_name": UserName,
		"user_id":   UserId,
		"dept_id":   DeptId,
		"exp":       time.Now().Unix() + int64(config2.Jwt.JwtTtl),
		"iss":       "thooh-go",
		"uuid":      uuid,
	})

	mySigningKey := []byte(config2.Jwt.Secret)

	return token.SignedString(mySigningKey)
}

func VerifyToken(tokenStr string) (*jwt.Token, error) {
	mySigningKey := []byte(config2.Jwt.Secret)
	tokenStr = strings.ReplaceAll(tokenStr, config2.HeaderSignTokenStr, "")
	return jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
		return mySigningKey, nil
	})
}

func JWTAuthMiddleware() func(ctx *gin.Context) {
	return func(ctx *gin.Context) {
		// 根据实际情况取TOKEN, 这里从request header取
		header := ctx.Request.Header
		tokenStr := header.Get(config2.HeaderSignToken)
		if len(tokenStr) < 1 {
			ctx.JSON(http.StatusOK, gin.H{
				"msg":  "令牌不能为空",
				"code": http.StatusInternalServerError,
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
		uuid := token.Claims.(jwt.MapClaims)["uuid"]
		loginUser, err := redisCache.NewRedisCache().Get(constants.LoginCacheKey + uuid.(string))
		if len(loginUser) <= 0 || err != nil {
			ctx.JSON(http.StatusOK, gin.H{
				"msg":  "认证失败",
				"code": http.StatusUnauthorized,
			})
			ctx.Abort()
			return
		}
		userId := token.Claims.(jwt.MapClaims)["user_id"]
		deptId := token.Claims.(jwt.MapClaims)["dept_id"]
		userName := token.Claims.(jwt.MapClaims)["user_name"]
		// 此处已经通过了, 可以把Claims中的有效信息拿出来放入上下文使用
		ctx.Set("userId", userId)
		ctx.Set("deptId", deptId)
		ctx.Set("userName", userName)
		ctx.Next()
	}
}

func GetJwtUuid(ctx *gin.Context) (string, error) {
	tokenStr := ctx.Request.Header.Get(config2.HeaderSignToken)
	if len(tokenStr) <= 0 {
		return "", nil
	}
	token, err := VerifyToken(tokenStr)
	if err != nil {
		return "", err
	}
	uuid := token.Claims.(jwt.MapClaims)["uuid"]
	return uuid.(string), nil

}
