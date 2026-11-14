package system

import (
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

type SysRoleMenu struct {
	RoleId int `json:"roleId" gorm:"column:rid"`
	MenuId int `json:"menuId" gorm:"column:mid"`
}

// TableName 指定数据库表名称
func (SysRoleMenu) TableName() string {
	return "sys_role_menu"
}

// 删除角色与菜单关联
func DeleteRoleMenu(roleIds string) {
	sql := "delete from sys_role_menu where rid in ( " + roleIds + " )"
	err := mysql.MysqlDb().Exec(sql).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
}

// 通过角色ID删除角色和菜单关联
func DeleteRoleMenuByRoleId(roleId string) {
	sql := "delete from sys_role_menu where rid = " + roleId
	err := mysql.MysqlDb().Exec(sql).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
}
