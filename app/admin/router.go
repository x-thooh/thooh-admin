package admin

import (
	"time"

	singlec "github.com/x-thooh/thooh-admin/admin/demo/single/cate"
	single "github.com/x-thooh/thooh-admin/admin/demo/single/main"
	api "github.com/x-thooh/thooh-admin/app/admin/api/system"
	"github.com/x-thooh/thooh-admin/app/admin/router/monitor"
	"github.com/x-thooh/thooh-admin/app/admin/router/system"
	"github.com/x-thooh/thooh-admin/app/admin/router/tools"
	"github.com/x-thooh/thooh-admin/app/core/utils/jwt"
	"github.com/x-thooh/thooh-admin/common/utils"
	"github.com/x-thooh/thooh-admin/modules/auth"
	lolog "github.com/x-thooh/thooh-admin/modules/mon/login"
	oplog "github.com/x-thooh/thooh-admin/modules/mon/oper"
	"github.com/x-thooh/thooh-admin/modules/pub"
	myapi "github.com/x-thooh/thooh-admin/modules/sys/api"
	"github.com/x-thooh/thooh-admin/modules/sys/config"
	"github.com/x-thooh/thooh-admin/modules/sys/group"
	"github.com/x-thooh/thooh-admin/modules/sys/groupc"
	"github.com/x-thooh/thooh-admin/modules/sys/menu"
	"github.com/x-thooh/thooh-admin/modules/sys/notice"
	"github.com/x-thooh/thooh-admin/modules/sys/org"
	"github.com/x-thooh/thooh-admin/modules/sys/post"
	"github.com/x-thooh/thooh-admin/modules/sys/role"
	"github.com/x-thooh/thooh-admin/modules/sys/user"
	dictd "github.com/x-thooh/thooh-admin/modules/tool/dict/data"
	dict "github.com/x-thooh/thooh-admin/modules/tool/dict/main"
	"github.com/x-thooh/thooh-admin/modules/tool/form"
	"github.com/x-thooh/thooh-admin/modules/tool/num"
	"github.com/x-thooh/thooh-admin/pkg/mysql"

	cache "github.com/chenyahui/gin-cache"
	"github.com/chenyahui/gin-cache/persist"
	"github.com/gin-gonic/gin"
)

func Routers(e *gin.Engine) {

	memoryStore := persist.NewMemoryStore(1 * time.Minute)
	handlerFunc := cache.CacheByRequestURI(memoryStore, 2*time.Second)

	e.GET("/index", api.IndexHandler)
	// 登录三件套改挂 modules（dump 口径：sys_user.id 是 varchar(36)）。
	// 旧那套的 LoginHandler 先留着不删，等 T-20e 按目录退役时一起清。
	e.GET("/captchaImage", auth.Code)
	e.POST("/login", auth.Login)
	e.POST("/logout", auth.Logout)
	v1 := e.Group("/")
	{
		auth := v1.Group("")
		auth.Use(jwt.JWTAuthMiddleware())
		{
			auth.GET("getInfo", handlerFunc, api.GetInfoHandler)
			/*获取用户授权菜单*/
			auth.GET("getRouters", handlerFunc, api.GetRoutersHandler)
		}
	}
	/*system*/
	system.InitProfile(e)
	system.InitDict(e)
	system.InitUser(e)
	system.InitMenu(e)
	system.InitPost(e)
	system.InitNotice(e)
	system.InitRole(e)
	system.InitConfig(e)
	system.InitDept(e)

	/*monitor*/
	monitor.InitCache(e)
	monitor.InitLogininfor(e)
	monitor.InitJob(e)
	monitor.InitJobLog(e)
	monitor.InitOnLine(e)
	monitor.InitOperlog(e)
	monitor.InitServer(e)

	/*tools*/
	tools.InitCommon(e)
	tools.InitGen(e)

	/*文件管理*/
	//file.InitFile(e)

	/*business业务路由*/
	utils.InitIdGenerator()
	auth.Init(e)
	pub.Init(e)

	/*sys*/
	org.Init(e)
	user.Init(e)
	post.Init(e)
	group.Init(e)
	groupc.Init(e)
	menu.Init(e)
	myapi.Init(e)
	role.Init(e)
	config.Init(e)
	notice.Init(e)

	/*tool*/
	form.Init(e)
	dict.Init(e)
	dictd.Init(e)
	num.Init(e)

	/*mon*/
	lolog.Init(e)
	oplog.Init(e)

	/*admin*/
	single.Init(e)
	singlec.Init(e)

	err := mysql.MysqlDb().AutoMigrate(&group.SysGroup{}, &groupc.SysGroupCate{}, &group.SysGroupActor{})
	if err != nil {
		return
	}

}
