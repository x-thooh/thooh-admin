package auth

import (
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/x-thooh/thooh-admin/app/admin/model/constants"
	"github.com/x-thooh/thooh-admin/common/config"
	sysconfig "github.com/x-thooh/thooh-admin/modules/sys/config"
	"github.com/x-thooh/thooh-admin/modules/sys/menu"
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

func findUserById(id string) (user.SysUser, error) {
	var u user.SysUser
	if err := mysql.MysqlDb().First(&u, "id = ? AND avtag = 1", id).Error; err != nil {
		return u, fmt.Errorf("按用户 ID %q 查 sys_user 失败：%w", id, err)
	}
	return u, nil
}

func findOrg(orgId string) *org.SysOrg {
	if orgId == "" {
		return nil
	}
	var o org.SysOrg
	if err := mysql.MysqlDb().First(&o, "id = ?", orgId).Error; err != nil {
		return nil
	}
	return &o
}

func findOrgName(orgId string) string {
	if o := findOrg(orgId); o != nil {
		return o.Name
	}
	return ""
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

// sys_menu.type 只有两种：目录（下面挂页面）与页面。常量放在用它的地方，
// 别学旧实现里散在条件里的 '1'/'2'。
const (
	dirType    = "1"
	pageType   = "2"
	noRedirect = "noRedirect"
	layout     = "Layout"
	parentView = "ParentView"
	innerLink  = "InnerLink"
)

// columnRow 给只回一列的查询兜 Scan 的目标：gorm 要把结果落到具名字段上，
// 而落点名字由 SQL 里的 `as value` 决定，两处得一致。
type columnRow struct {
	Value string
}

func columnValues(sql string, args ...any) ([]string, error) {
	var rows []columnRow
	if err := mysql.MysqlDb().Raw(sql, args...).Scan(&rows).Error; err != nil {
		return nil, err
	}
	values := make([]string, 0, len(rows))
	for _, row := range rows {
		if row.Value != "" {
			values = append(values, row.Value)
		}
	}
	return values, nil
}

// roleNames 与 permissionCodes 走的是同一条链：参与者（sys_role_actor.aid 就是用户 id）
// → 可用角色 → 角色授到的菜单/接口。没有「超级管理员」这种代码里的特判：
// 权限由数据给，dump 里 u1 靠 sys_role_actor(1,'u1') 拿到「管理员」角色。
func roleNames(userId string) ([]string, error) {
	return columnValues(`select r.name as value from sys_role r
		join sys_role_actor ra on ra.rid = r.id
		where ra.aid = ? and r.avtag = 1 order by r.ornum`, userId)
}

func permissionCodes(userId string) ([]string, error) {
	return columnValues(`select distinct a.perm as value from sys_role_actor ra
		join sys_role r on r.id = ra.rid and r.avtag = 1
		join sys_role_api rpa on rpa.rid = r.id
		join sys_api a on a.id = rpa.aid and a.avtag = 1
		where ra.aid = ? and a.perm is not null order by a.perm`, userId)
}

// grantedMenus 返回这个人的角色被授到的所有菜单行（含隐藏的详情页），
// 目录与页面都要：目录决定树的结构，砍了就只剩一堆孤儿子页。
func grantedMenus(userId string) ([]menu.SysMenu, error) {
	var list []menu.SysMenu
	sql := `select distinct m.id, m.pid, m.name, m.type, m.icon, m.path, m.param, m.comp, m.ornum,
	        m.shtag, m.catag, m.outag from sys_menu m
		join sys_role_menu rm on rm.mid = m.id
		join sys_role r on r.id = rm.rid and r.avtag = 1
		join sys_role_actor ra on ra.rid = r.id
		where ra.aid = ? and m.avtag = 1 order by m.pid, m.ornum`
	if err := mysql.MysqlDb().Raw(sql, userId).Scan(&list).Error; err != nil {
		return nil, fmt.Errorf("按用户 ID %q 查授权菜单失败：%w", userId, err)
	}
	return list, nil
}

func buildRouters(granted []menu.SysMenu) []RouterVo {
	routers := make([]RouterVo, 0, len(granted))
	for _, m := range granted {
		if m.Pid != 0 {
			continue
		}
		if m.Type == pageType && !bool(m.Outag) {
			routers = append(routers, menuFrameRouter(m))
			continue
		}
		router := routerOf(m)
		children := childRouters(m.Id, granted)
		if len(children) == 0 {
			// 授了目录却一条子页也没授：点进去是白页，不如不出现。
			// 外链目录自己就是页面，例外。
			if m.Type != dirType || componentOf(m) != innerLink {
				continue
			}
		} else {
			router.AlwaysShow = true
			router.Redirect = noRedirect
			router.Children = children
		}
		routers = append(routers, router)
	}
	return routers
}

func childRouters(parentId int64, granted []menu.SysMenu) []RouterVo {
	children := make([]RouterVo, 0, len(granted))
	for _, m := range granted {
		if m.Pid != parentId {
			continue
		}
		router := routerOf(m)
		if grandchildren := childRouters(m.Id, granted); len(grandchildren) > 0 {
			router.AlwaysShow = true
			router.Redirect = noRedirect
			router.Children = grandchildren
		}
		children = append(children, router)
	}
	return children
}

func routerOf(m menu.SysMenu) RouterVo {
	link := ""
	if isInnerLink(m.Path) {
		link = m.Path
	}
	return RouterVo{
		Name:      routeName(m),
		Path:      routePath(m),
		Hidden:    !bool(m.Shtag),
		Component: componentOf(m),
		Query:     m.Param,
		Meta:      MetaVo{Title: m.Name, Icon: m.Icon, NoCache: bool(m.Catag), Link: link},
	}
}

// menuFrameRouter：一级页面（没有目录包着）。vue-router 的顶层路由要有布局组件，
// 所以套一层 Layout，真页面做成它的子路由——和 modules/pub 的做法一致。
func menuFrameRouter(m menu.SysMenu) RouterVo {
	page := routerOf(m)
	page.Name = upperFirst(m.Path)
	page.Path = m.Path
	return RouterVo{
		Path:      "/",
		Component: layout,
		Hidden:    page.Hidden,
		Meta:      MetaVo{Title: m.Name, Icon: m.Icon, NoCache: bool(m.Catag)},
		Children:  []RouterVo{page},
	}
}

func routeName(m menu.SysMenu) string {
	if m.Pid == 0 && m.Type == pageType && !bool(m.Outag) {
		return ""
	}
	return upperFirst(m.Path)
}

func routePath(m menu.SysMenu) string {
	if isInnerLink(m.Path) {
		return m.Path
	}
	if m.Pid == 0 && m.Type == dirType && !bool(m.Outag) {
		return "/" + m.Path
	}
	if m.Pid == 0 && m.Type == pageType && !bool(m.Outag) {
		return "/"
	}
	return m.Path
}

func componentOf(m menu.SysMenu) string {
	if m.Comp != "" && !isMenuFrame(m) {
		return m.Comp
	}
	if m.Comp == "" && isInnerLink(m.Path) {
		return innerLink
	}
	if m.Comp == "" && m.Pid != 0 && m.Type == dirType {
		return parentView
	}
	return layout
}

func isMenuFrame(m menu.SysMenu) bool {
	return m.Pid == 0 && m.Type == pageType && !bool(m.Outag)
}

func isInnerLink(path string) bool {
	return strings.Contains(path, "http://") || strings.Contains(path, "https://")
}

func upperFirst(s string) string {
	if s == "" {
		return s
	}
	return strings.ToUpper(s[:1]) + s[1:]
}
