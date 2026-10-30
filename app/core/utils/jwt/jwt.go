package jwt

import (
	config2 "github.com/x-thooh/thooh-admin/common/config"
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

// JWTAuthMiddleware 保留这个名字是给已经按组挂载的地方用的；实现只有 Gate 一份，
// 免得「组级鉴权」与「全局门」两套姿势走偏。
func JWTAuthMiddleware() func(ctx *gin.Context) {
	return Gate()
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
