package system

import (
	"github.com/x-thooh/thooh-admin/app/admin/model/tools"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

// SysUserRole model：数据库字段
type SysUserRole struct {
	UserId string `json:"userId" gorm:"column:aid"` //表示主键
	RoleId int    `json:"roleId" gorm:"column:rid"`
}

// TableName 指定数据库表名称
func (SysUserRole) TableName() string {
	return "sys_role_actor"
}

type SysUserRolesParam struct {
	RoleId int    `json:"roleId"`
	UserId string `json:"userId"`
}

// 分页查询
func SelectSysUserRoleList(params tools.SearchTableDataParam, isPage bool) tools.TableDataInfo {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysUserRole := params.Other.(SysUserRole)

	offset := (pageNum - 1) * pageSize
	var total int64
	var rows []SysUserRole

	var db = mysql.MysqlDb().Model(&SysUserRole{}).
		Joins("left join sys_org d on d.id = id").
		Select("*, d.name")

	db.Where("1 = 1")
	var userId = sysUserRole.UserId
	if userId != "" {
		db.Where("aid = ?", userId)
	}
	if err := db.Count(&total).Error; err != nil {
		return tools.Fail()
	}
	if isPage {
		if err := db.Limit(pageSize).Offset(offset).Find(&rows).Error; err != nil {
			return tools.Fail()
		}
	} else {
		if err := db.Find(&rows).Error; err != nil {
			return tools.Fail()
		}
	}

	if rows == nil {
		return tools.Fail()
	} else {
		return tools.Success(rows, total)
	}
}
