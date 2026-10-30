package auth

import (
	"encoding/json"
	"fmt"
	"strconv"
	"time"

	"github.com/x-thooh/thooh-admin/app/admin/model/constants"
	"github.com/x-thooh/thooh-admin/common/config"
	sysconfig "github.com/x-thooh/thooh-admin/modules/sys/config"
	"github.com/x-thooh/thooh-admin/modules/sys/org"
	"github.com/x-thooh/thooh-admin/modules/sys/user"
	"github.com/x-thooh/thooh-admin/pkg/cache/redisCache"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

// constants.LoginCacheKey 与鉴权中间件（app/core/utils/jwt）共用同一个 redis 键前缀。
// 键对不上就等于「登录成功但每个受保护请求都认证失败」，所以这里宁可从旧目录引这一个常量。
// 旧实现退役时把常量搬到 common，这条注释一起删。

func findUser(username string) (user.SysUser, error) {
	var u user.SysUser
	// avtag 是 dump 里的可用标记；旧那套的 del_flag / status 两列在这张表里不存在
	err := mysql.MysqlDb().Where("username = ? AND avtag = 1", username).First(&u).Error
	if err != nil {
		return u, fmt.Errorf("按用户名 %q 查 sys_user 失败：%w", username, err)
	}
	return u, nil
}

func findOrgName(orgId string) string {
	if orgId == "" {
		return ""
	}
	var o org.SysOrg
	if err := mysql.MysqlDb().First(&o, "id = ?", orgId).Error; err != nil {
		return ""
	}
	return o.Name
}

// captchaEnabled 读不到或读不懂都算「要验证码」：这是失败往安全那一档走，
// 客户库里少一行配置不该把验证码门悄悄打开。
func captchaEnabled() bool {
	var cfg sysconfig.SysConfig
	if err := mysql.MysqlDb().First(&cfg, "kenam = ?", "sys.account.captchaEnabled").Error; err != nil {
		return true
	}
	enabled, err := strconv.ParseBool(cfg.Keval)
	if err != nil {
		return true
	}
	return enabled
}

func saveSession(s Session) error {
	data, err := json.Marshal(s)
	if err != nil {
		return fmt.Errorf("会话编码失败：%w", err)
	}
	ttl := time.Duration(config.Jwt.JwtTtl) * time.Second
	if err := redisCache.NewRedisCache().Put(constants.LoginCacheKey+s.TokenId, string(data), ttl); err != nil {
		return fmt.Errorf("会话写入 redis 失败：%w", err)
	}
	return nil
}

func dropSession(tokenId string) {
	redisCache.NewRedisCache().Del(constants.LoginCacheKey + tokenId)
}
