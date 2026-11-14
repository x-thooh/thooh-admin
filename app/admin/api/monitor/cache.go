package monitor

import (
	stdctx "context"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/x-thooh/thooh-admin/app/admin/model/constants"
	"github.com/x-thooh/thooh-admin/app/admin/model/monitor"
	"github.com/x-thooh/thooh-admin/pkg/cache/redisCache"
	"github.com/x-thooh/thooh-admin/pkg/redis"
)

func cacheNameList() []monitor.SysCache {
	var list []monitor.SysCache
	list = append(list, monitor.SysCache{
		CacheName: constants.LoginCacheKey,
		Remark:    "用户信息",
	})
	list = append(list, monitor.SysCache{
		CacheName: "sys_config:",
		Remark:    "配置信息",
	})
	list = append(list, monitor.SysCache{
		CacheName: constants.SysDictCacheKey,
		Remark:    "数据字典",
	})
	list = append(list, monitor.SysCache{
		CacheName: "captcha_codes:",
		Remark:    "验证码",
	})
	list = append(list, monitor.SysCache{
		CacheName: "repeat_submit:",
		Remark:    "防重提交",
	})
	list = append(list, monitor.SysCache{
		CacheName: "rate_limit:",
		Remark:    "限流处理",
	})
	list = append(list, monitor.SysCache{
		CacheName: "pwd_err_cnt:",
		Remark:    "密码错误次数",
	})
	return list
}

func CacheHandler(context *gin.Context) {
	// WHY: 缓存页前端直接读 cache.info.used_memory_human 画仪表盘（产物里 tooltip 的 formatter
	// 没有做空值保护），不返回 info 就在渲染时抛 TypeError（浏览器实测）。
	info := map[string]string{}
	if raw, err := redis.Client().Info(stdctx.TODO()).Result(); err == nil {
		for _, line := range strings.Split(raw, "\r\n") {
			if k, v, ok := strings.Cut(line, ":"); ok && v != "" {
				info[k] = v
			}
		}
	}
	dbSize, _ := redis.Client().DBSize(stdctx.TODO()).Result()
	// WHY: 缓存页前端把响应的 data 直接当 cache 对象用（读 cache.info.used_memory_human、
	// cache.dbSize），名字列表另有 getNames 接口。把 data 写成 info 对象才与产物契约一致；
	// 之前返回数组 → cache.info 为 undefined → 渲染时抛 TypeError（浏览器实测）。
	context.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
		"data": gin.H{
			"info":         info,
			"dbSize":       dbSize,
			"commandStats": []any{},
		},
	})
}

// CacheNamesHandler 返回可清理的缓存名前缀列表（前端缓存页左侧表格）
func CacheNamesHandler(context *gin.Context) {
	list := cacheNameList()
	context.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
		"data": list,
	})
}

func GetCacheKeysHandler(context *gin.Context) {
	cacheName := context.Param("cacheName")
	keys, _, err := redisCache.NewRedisCache().Scan(0, cacheName+"*", constants.ScanCountMax)
	if err != nil {
		context.JSON(http.StatusOK, gin.H{
			"msg":  err.Error(),
			"code": http.StatusInternalServerError,
		})
	}
	context.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
		"data": keys,
	})
}

func GetCacheValueHandler(context *gin.Context) {
	cacheName := context.Param("cacheName")
	cacheKey := context.Param("cacheKey")
	value, err := redisCache.NewRedisCache().Get(cacheKey)
	if err != nil {
		context.JSON(http.StatusOK, gin.H{
			"msg":  err.Error(),
			"code": http.StatusInternalServerError,
		})
	}
	var cache = monitor.SysCache{
		CacheName:  cacheName,
		CacheKey:   cacheKey,
		CacheValue: value,
	}
	context.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
		"data": cache,
	})
}

func ClearCacheNameHandler(context *gin.Context) {
	cacheName := context.Param("cacheName")
	keys, _, err := redisCache.NewRedisCache().Scan(0, cacheName+"*", constants.ScanCountMax)
	if err != nil {
		context.JSON(http.StatusOK, gin.H{
			"msg":  err.Error(),
			"code": http.StatusInternalServerError,
		})
	}
	for i := range keys {
		redisCache.NewRedisCache().Del(keys[i])
	}
	context.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
	})
}

func ClearCacheKeyHandler(context *gin.Context) {
	cacheKey := context.Param("cacheKey")
	_, err := redisCache.NewRedisCache().Del(cacheKey)
	if err != nil {
		context.JSON(http.StatusOK, gin.H{
			"msg":  err.Error(),
			"code": http.StatusInternalServerError,
		})
		return
	}
	context.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
	})
}

func ClearCacheAllHandler(context *gin.Context) {
	keys, _, err := redisCache.NewRedisCache().Scan(0, "*", constants.ScanCountMax)
	if err != nil {
		context.JSON(http.StatusOK, gin.H{
			"msg":  err.Error(),
			"code": http.StatusInternalServerError,
		})
	}
	for i := range keys {
		redisCache.NewRedisCache().Del(keys[i])
	}
	context.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
	})
}
