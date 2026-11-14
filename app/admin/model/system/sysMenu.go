package system

import (
	"strconv"
	"strings"
	"time"

	"github.com/x-thooh/thooh-admin/app/admin/model/tools"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

// SysMenu model：数据库字段
type SysMenu struct {
	MenuId     int       `json:"menuId" gorm:"column:id;primaryKey"` //表示主键
	MenuName   string    `json:"menuName" gorm:"column:name"`
	ParentId   int       `json:"parentId" gorm:"column:pid"`
	OrderNum   int       `json:"orderNum" gorm:"column:ornum"`
	MenuType   string    `json:"menuType" gorm:"column:type"`
	Visible    string    `json:"visible" gorm:"column:shtag"`
	Perms      string    `json:"perms" gorm:"-"`
	Query      string    `json:"query" gorm:"column:param"`
	IsFrame    string    `json:"isFrame" gorm:"column:outag"`
	Icon       string    `json:"icon" gorm:"column:icon"`
	Path       string    `json:"path" gorm:"column:path"`
	Status     string    `json:"status" gorm:"column:avtag"`
	IsCache    string    `json:"isCache" gorm:"column:catag"`
	Component  string    `json:"component" gorm:"column:comp"`
	CreateBy   string    `json:"createBy" gorm:"-"`
	CreateTime time.Time `json:"createTime" gorm:"column:crtim;type:datetime;autoCreateTime"`
	UpdateBy   string    `json:"updateBy" gorm:"-"`
	UpdateTime time.Time `json:"updateTime" gorm:"column:uptim;type:datetime;autoCreateTime"`
	Remark     string    `json:"remark" gorm:"column:notes"`
}

type MenuVo struct {
	Name       string   `json:"name"`
	Path       string   `json:"path,omitempty"`
	Hidden     bool     `json:"hidden" `
	Redirect   string   `json:"redirect,omitempty"`
	Component  string   `json:"component,omitempty" `
	Query      string   `json:"query,omitempty"`
	AlwaysShow bool     `json:"alwaysShow,omitempty" `
	MetaVo     MetaVo   `json:"meta" `
	Children   []MenuVo `json:"children,omitempty"`
}

type MetaVo struct {
	Title   string `json:"title"`
	Icon    string `json:"icon" `
	NoCache bool   `json:"noCache" `
	Link    string `json:"link,omitempty" `
}

type MenuTreeSelect struct {
	Id       int              `json:"id"`
	Label    string           `json:"label"`
	Children []MenuTreeSelect `json:"children,omitempty"`
}

// TableName 指定数据库表名称
func (SysMenu) TableName() string {
	return "sys_menu"
}

func SelectMenuTreeByUserId(userId string) []SysMenu {
	var menu []SysMenu
	if IsAdminById(userId) {
		err := mysql.MysqlDb().Where("type in (?) ", []string{"M", "C"}).Where("avtag", "0").Order("pid").Order("ornum").Find(&menu).Error
		if err != nil {
			panic(R.ReturnFailMsg("查询错误"))
		}
	} else {
		err := mysql.MysqlDb().Raw("select distinct m.* from sys_menu m left join sys_role_menu rm on m.id = rm.mid left join sys_role_actor ur on rm.rid = ur.rid left join sys_role ro on ur.rid = ro.id left join sys_user u on ur.aid = u.id where u.id = ? and m.type in ('M', 'C') and m.avtag = 0  AND ro.avtag = 0 order by m.pid, m.ornum", userId).Scan(&menu).Error
		if err != nil {
			panic(R.ReturnFailMsg("查询错误"))
		}
	}
	return menu
}

func SelectMenuTree(userId string, menu SysMenu) []SysMenu {
	var menus []SysMenu
	sql := "select distinct m.id, m.pid, m.name, m.path, m.comp, m.param, m.shtag, m.avtag, '' as perms, m.outag, m.catag, m.type, m.icon, m.ornum, m.crtim "
	sql += "from sys_menu m "
	if IsAdminById(userId) {
		var menuName = menu.MenuName
		if menuName != "" {
			sql += "AND m.name like concat('%', " + menuName + ", '%')"
		}
		var visible = menu.Visible
		if visible != "" {
			sql += "AND m.shtag = " + visible
		}
		var status = menu.Status
		if status != "" {
			sql += "AND m.avtag = " + status
		}
		err := mysql.MysqlDb().Raw(sql).Scan(&menus).Error
		if err != nil {
			panic(R.ReturnFailMsg(err.Error()))
		}
	} else {
		sql += "left join sys_role_menu rm on m.id = rm.mid "
		sql += "left join sys_role_actor ur on rm.rid = ur.rid "
		sql += "left join sys_role ro on ur.rid = ro.id "
		sql += "where ur.aid = '" + userId + "'"
		var menuName = menu.MenuName
		if menuName != "" {
			sql += "AND m.name like concat('%', " + menuName + ", '%')"
		}
		var visible = menu.Visible
		if visible != "" {
			sql += "AND m.shtag = " + visible
		}
		var status = menu.Status
		if status != "" {
			sql += "AND m.avtag = " + status
		}
		err := mysql.MysqlDb().Raw(sql).Scan(&menus).Error
		if err != nil {
			panic(R.ReturnFailMsg(err.Error()))
		}
	}
	return menus
}

func BuildMenuTreeSelect(lists []SysMenu) []MenuTreeSelect {
	var menuTreeSelect []MenuTreeSelect
	for i := 0; i < len(lists); i++ {
		var menu = lists[i]
		menuId := menu.MenuId
		parentId := menu.ParentId
		if 0 == parentId {
			var menuVo = MenuTreeSelect{
				Id:    menuId,
				Label: menu.MenuName,
			}
			menuVo.Children = BuildChildMenusTreeSelect(menuId, lists)
			menuTreeSelect = append(menuTreeSelect, menuVo)
		}
	}
	return menuTreeSelect
}

func BuildChildMenusTreeSelect(ParentId int, lists []SysMenu) []MenuTreeSelect {
	var List []MenuTreeSelect
	for i := 0; i < len(lists); i++ {
		var menu = lists[i]
		var menuId = menu.MenuId
		var pId = menu.ParentId
		if pId == ParentId {
			var menuVo = MenuTreeSelect{
				Id:    menuId,
				Label: menu.MenuName,
			}
			menuVo.Children = BuildChildMenusTreeSelect(menuId, lists)
			List = append(List, menuVo)
		}
	}
	return List
}

func BuildMenus(lists []SysMenu) []MenuVo {
	var menuVos []MenuVo
	for i := 0; i < len(lists); i++ {
		var menu = lists[i]
		MenuId := menu.MenuId
		parentId := menu.ParentId
		if 0 == parentId {
			var path = ""
			if isInnerLink(menu.Path) {
				path = menu.Path
			}
			var menuVo = MenuVo{
				Hidden: "1" == menu.Visible,
				Query:  menu.Query,
				MetaVo: MetaVo{
					Title:   menu.MenuName,
					Icon:    menu.Icon,
					NoCache: "1" == menu.IsCache,
					Link:    path,
				},
				Name:      getRouteName(menu),
				Path:      getRouterPath(menu),
				Component: getComponent(menu),
			}
			if "M" == menu.MenuType {
				if !isInnerLink(menu.Path) {
					menuVo.AlwaysShow = true
					menuVo.Redirect = "noRedirect"
					menuVo.Children = BuildChildMenus(MenuId, lists)
				}
			}
			menuVos = append(menuVos, menuVo)
		}

	}
	return menuVos
}

func BuildChildMenus(ParentId int, lists []SysMenu) []MenuVo {
	var List []MenuVo
	for i := 0; i < len(lists); i++ {
		var menu = lists[i]
		var menuId = menu.MenuId
		var pId = menu.ParentId
		if pId == ParentId {
			var path = ""
			if isInnerLink(menu.Path) {
				path = menu.Path
			}
			var menuVo = MenuVo{
				Hidden: "1" == menu.Visible,
				Query:  menu.Query,
				MetaVo: MetaVo{
					Title:   menu.MenuName,
					Icon:    menu.Icon,
					NoCache: "1" == menu.IsCache,
					Link:    path,
				},
				Name:      getRouteName(menu),
				Path:      getRouterPath(menu),
				Component: getComponent(menu),
			}
			if "M" == menu.MenuType {
				if !isInnerLink(menu.Path) {
					menuVo.AlwaysShow = true
					menuVo.Redirect = "noRedirect"
					menuVo.Children = BuildChildMenus(menuId, lists)
				}
			}
			List = append(List, menuVo)
		}
	}
	return List
}

func getRouteName(menu SysMenu) string {
	var name = FirstUpper(menu.Path)
	if isMenuFrame(menu) {
		return ""
	}
	return name
}

func getRouterPath(menu SysMenu) string {
	var routerPath = menu.Path
	if isInnerLink(routerPath) {
		return routerPath
	}
	// 非外链并且是一级目录（类型为目录）
	if 0 == menu.ParentId && "M" == menu.MenuType && "1" == menu.IsFrame {
		routerPath = "/" + menu.Path
	} else if isMenuFrame(menu) {
		routerPath = "/"
	}
	return routerPath
}

func getComponent(menu SysMenu) string {
	var component = "Layout"
	if "" != menu.Component && !isMenuFrame(menu) {
		component = menu.Component
	} else if "" == menu.Component && isInnerLink(menu.Path) {
		component = "InnerLink"
	} else if "" == menu.Component && isParentView(menu) {
		component = "ParentView"
	}
	return component
}

func isParentView(menu SysMenu) bool {
	return menu.ParentId != 0 && "M" == menu.MenuType
}

// 是否为外链
func isInnerLink(path string) bool {
	return strings.Contains(path, "http://") || strings.Contains(path, "https://")
}

func isMenuFrame(menu SysMenu) bool {
	return menu.ParentId == 0 && "C" == menu.MenuType && menu.IsFrame == "1"
}

/*首字母大写*/
func FirstUpper(s string) string {
	if s == "" {
		return ""
	}
	return strings.ToUpper(s[:1]) + s[1:]
}

// SelectSysMenuList /*分页查询*/
func SelectSysMenuList(params tools.SearchTableDataParam) []SysMenu {
	sysMenu := params.Other.(SysMenu)
	var rows []SysMenu
	var sql = "select id, name, pid, ornum, path, comp, param, outag, catag, type, shtag, " +
		"avtag, '' as perms, icon, crtim from sys_menu where 1 = 1 "
	var name = sysMenu.MenuName
	if name != "" {
		sql += " AND name LIKE CONCAT('%', '" + name + "', '%')"
	}
	var visible = sysMenu.Visible
	if visible != "" {
		sql += " AND shtag = " + visible
	}
	var status = sysMenu.Status
	if status != "" {
		sql += " AND avtag = " + status
	}
	err := mysql.MysqlDb().Raw(sql).Find(&rows).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return rows
}

func SelectMenuListByRoleId(roleId string, menuCheckStrictly bool) []int {
	var sql = "select m.id from sys_menu m " +
		"left join sys_role_menu rm on m.id = rm.mid " +
		"where rm.rid = " + roleId + " "
	if menuCheckStrictly {
		sql += "and m.id not in (select m.pid from sys_menu m inner join sys_role_menu rm on m.id = rm.mid and rm.rid = " + roleId + ")"
	}
	sql += "order by m.pid, m.ornum"
	var menuIds []int
	err := mysql.MysqlDb().Raw(sql).Scan(&menuIds).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return menuIds
}

func SelectSysMenuListByUserId(userId string, params tools.SearchTableDataParam) []SysMenu {
	sysMenu := params.Other.(SysMenu)
	var sql = "select distinct m.id, m.pid, m.name, m.path, m.comp, m.param, m.shtag," +
		" m.avtag, '' as perms, m.outag, m.catag, m.type, m.icon, m.ornum, m.crtim " +
		"from sys_menu m left join sys_role_menu rm on m.id = rm.mid " +
		"left join sys_role_actor ur on rm.rid = ur.rid " +
		"left join sys_role ro on ur.rid = ro.id "

	sql += "where ur.aid = '" + userId + "' "
	var menuName = sysMenu.MenuName
	if menuName != "" {
		sql += "AND m.name like concat(%" + menuName + "%) "
	}
	var visible = sysMenu.Visible

	if visible != "" {
		sql += "AND m.shtag = " + visible + " "
	}
	var status = sysMenu.Status
	if status != "" {
		sql += "AND m.avtag = " + status + " "
	}

	sql += "order by m.pid, m.ornum"
	var list []SysMenu
	err := mysql.MysqlDb().Raw(sql).Scan(&list).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return list
}

func FindMenuInfoById(menuId string) SysMenu {
	sql := "select id, name, pid, ornum, path, " +
		"comp, param, outag, catag, type, shtag, avtag, '' as perms, icon, crtim " +
		"from sys_menu "
	sql = sql + "where id = " + menuId
	var list SysMenu
	err := mysql.MysqlDb().Raw(sql).First(&list).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return list
}

func hasChildByMenuId(menuId string) SysMenu {
	var menu SysMenu
	mysql.MysqlDb().Where("pid = ? ", menuId).First(&menu)
	return menu
}

func hasChildCountByMenuId(menuId string) int {
	var menuCount int
	err := mysql.MysqlDb().Where("pid = ? ", menuId).Scan(&menuCount).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return menuCount
}

func checkMenuExistRole(menuId string) int {
	var menuCount int
	err := mysql.MysqlDb().Raw("select count(1) from sys_role_menu where id = " + menuId).Scan(&menuCount).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return menuCount
}

func DeleteMenu(menuIds string) R.Result {
	menu := hasChildByMenuId(menuIds)
	if menu.MenuId != 0 {
		return R.ReturnFailMsg("存在子菜单,不允许删除")
	}

	menuCount := checkMenuExistRole(menuIds)
	if menuCount > 0 {
		return R.ReturnFailMsg("菜单已分配,不允许删除")
	}

	err := mysql.MysqlDb().Exec("delete from sys_menu where id in (?) ", menuIds).Error
	if err == nil {
		R.ReturnFailMsg("删除部门关联用户失败")
	}
	return R.ReturnSuccess("操作成功")
}

func checkMenuNameUnique(parentId int, menuName string) int {
	var menuCount int
	err := mysql.MysqlDb().Raw("select count(1) from sys_menu where name = "+menuName+" and pid = "+strconv.Itoa(parentId), &menuCount).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return menuCount
}

func AddMenu(sysMenu SysMenu) R.Result {
	count := checkMenuNameUnique(sysMenu.ParentId, sysMenu.MenuName)
	if count > 0 {
		return R.ReturnFailMsg("新增菜单" + sysMenu.MenuName + "失败，菜单名称已存在")
	}
	menuPath := sysMenu.Path
	isFrame := sysMenu.IsFrame
	isPath := isInnerLink(menuPath)
	if isFrame == "true" && !isPath {
		return R.ReturnFailMsg("新增菜单" + sysMenu.MenuName + "失败，地址必须以http(s)://开头")
	}
	err := mysql.MysqlDb().Create(&sysMenu).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess("操作成功")

}

func UpdateMenu(sysMenu SysMenu) R.Result {
	mId := sysMenu.MenuId
	pId := sysMenu.ParentId
	if pId == mId {
		return R.ReturnFailMsg("修改菜单" + sysMenu.MenuName + "失败，上级菜单不能选择自己")
	}
	count := checkMenuNameUnique(pId, sysMenu.MenuName)
	if count > 0 {
		return R.ReturnFailMsg("修改菜单失败，菜单名称已存在" + sysMenu.MenuName + "失败，菜单名称已存在")
	}
	isFrame := sysMenu.IsFrame
	menuPath := sysMenu.Path
	isPath := isInnerLink(menuPath)
	if isFrame == "true" && !isPath {
		return R.ReturnFailMsg("修改菜单" + sysMenu.MenuName + "失败，地址必须以http(s)://开头")
	}
	err := mysql.MysqlDb().Updates(&sysMenu).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess("操作成功")
}
