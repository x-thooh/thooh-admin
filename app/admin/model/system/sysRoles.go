package system

import (
	"github.com/jinzhu/copier"
	"github.com/x-thooh/thooh-admin/app/admin/model/tools"
	utils2 "github.com/x-thooh/thooh-admin/app/core/utils"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
	"strconv"
	"time"
)

// SysRoles model：数据库字段
type SysRoles struct {
	RoleId            int       `json:"roleId" gorm:"column:id;primaryKey"` //表示主键
	RoleName          string    `json:"roleName" gorm:"column:name"`
	RoleKey           string    `json:"roleKey" gorm:"-"`
	RoleSort          int       `json:"roleSort" gorm:"column:ornum"`
	DataScope         string    `json:"dataScope" gorm:"column:scope"`
	Status            string    `json:"status" gorm:"column:avtag"`
	MenuCheckStrictly bool      `json:"menuCheckStrictly" gorm:"-"`
	DeptCheckStrictly bool      `json:"deptCheckStrictly" gorm:"-"`
	DelFlag           string    `json:"delFlag" gorm:"-"`
	CreateBy          string    `json:"createBy" gorm:"-"`
	CreateTime        time.Time `json:"createTime" gorm:"column:crtim;type:datetime;autoCreateTime"`
	UpdateBy          string    `json:"updateBy" gorm:"-"`
	UpdateTime        time.Time `json:"updateTime" gorm:"column:uptim;type:datetime;autoCreateTime"`
	Remark            string    `json:"remark" gorm:"column:notes"`
}

type SysRolesParam struct {
	RoleId            int       `json:"roleId" gorm:"column:id;primaryKey"` //表示主键
	RoleName          string    `json:"roleName" gorm:"column:name"`
	RoleKey           string    `json:"roleKey" gorm:"-"`
	RoleSort          int       `json:"roleSort" gorm:"column:ornum"`
	DataScope         string    `json:"dataScope" gorm:"column:scope"`
	Status            string    `json:"status" gorm:"column:avtag"`
	MenuCheckStrictly bool      `json:"menuCheckStrictly" gorm:"-"`
	DeptCheckStrictly bool      `json:"deptCheckStrictly" gorm:"-"`
	DelFlag           string    `json:"delFlag" gorm:"-"`
	CreateBy          string    `json:"createBy" gorm:"-"`
	CreateTime        time.Time `json:"createTime" gorm:"column:crtim;type:datetime"`
	UpdateBy          string    `json:"updateBy" gorm:"-"`
	UpdateTime        time.Time `json:"updateTime" gorm:"column:uptim;type:datetime"`
	Remark            string    `json:"remark" gorm:"column:notes"`
	MenuIds           []int     `json:"menuIds"`
	DeptIds           []int     `json:"deptIds"`
}

// TableName 指定数据库表名称
func (SysRoles) TableName() string {
	return "sys_role"
}

func SelectRolePermissionByUserId(userId int) []SysRoles {
	var roles []SysRoles
	var sql = "select distinct r.* " +
		"from sys_role r " +
		"left join sys_role_actor ur on ur.rid = r.id " +
		"left join sys_user u on u.id = ur.aid " +
		"left join sys_org d on u.orgid = d.id " +
		"where 1=1"
	if userId != 0 {
		if !IsAdminById(userId) {
			sql += " and ur.aid = " + strconv.Itoa(userId)
		}
	}
	err := mysql.MysqlDb().Raw(sql).Scan(&roles).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return roles
}

func buildRolePermissionByUserId(userId int) []string {
	var roles = SelectRolePermissionByUserId(userId)
	var roleNames []string
	for i := 0; i < len(roles); i++ {
		var role = roles[i]
		var roleName = role.RoleName
		roleNames = append(roleNames, roleName)
	}
	return roleNames
}

func GetRolePermission(user SysUser) []string {
	return GetRolePermissionById(user.UserId)
}

func GetRolePermissionById(userId int) []string {
	if IsAdminById(userId) {
		return []string{"admin"}
	} else {
		return buildRolePermissionByUserId(userId)
	}
}

func GetMenuPermission(user SysUser) []string {
	if IsAdmin(&user) {
		return []string{"*:*:*"}
	} else {
		var permissions []string
		err := mysql.MysqlDb().Raw("select distinct m.perms "+
			"from sys_menu m "+
			"left join sys_role_menu rm on m.menu_id = rm.menu_id "+
			"left join sys_role_actor ur on rm.rid = ur.rid "+
			"left join sys_role r on r.id = ur.rid "+
			"where m.avtag = 0 and r.avtag = 0 and ur.aid = ?", user.UserId).
			Scan(&permissions).Error
		if err != nil {
			panic(R.ReturnFailMsg(err.Error()))
		}
		return utils2.RemoveEmpty(permissions)
	}
}

func SelectRolesByUserName(userName string) string {
	var roles []SysRoles
	var result = ""
	err := mysql.MysqlDb().Raw("select distinct r.* "+
		"from sys_role r "+
		"left join sys_role_actor ur on ur.rid = r.id "+
		"left join sys_user u on u.id = ur.aid "+
		"left join sys_org d on u.orgid = d.id "+
		"WHERE u.username = ?", userName).
		Scan(&roles).
		Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	if roles != nil {
		for i := range roles {
			sysRoles := roles[i]
			if i == 0 {
				result = sysRoles.RoleName
			} else {
				result += "," + sysRoles.RoleName
			}
		}
	}
	return result
}

// 分页查询
func SelectRoleList(params tools.SearchTableDataParam, isPage bool) tools.TableDataInfo {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysRoles := params.Other.(SysRoles)

	offset := (pageNum - 1) * pageSize
	var total int64
	var rows []SysRoles
	var db = mysql.MysqlDb().Model(&rows).
		Select("distinct `sys_role`.*").
		Joins("left join sys_role_actor ur on ur.rid = `sys_role`.id").
		Joins("left join sys_user u on u.id = ur.aid").
		Joins("left join sys_org d on u.orgid = d.id")

	db.Where("1 = 1")
	var roleId = sysRoles.RoleId
	if roleId != 0 {
		db.Where("`sys_role`.id = ?", roleId)
	}

	var roleName = sysRoles.RoleName
	if roleName != "" {
		db.Where("`sys_role`.role_name like ?", "%"+roleName+"%")
	}

	var status = sysRoles.Status
	if status != "" {
		db.Where("`sys_role`.avtag = ?", status)
	}

	var beginTime = params.Params.BeginTime
	var endTime = params.Params.EndTime

	if beginTime != "" {
		//Loc, _ := time.LoadLocation("Asia/Shanghai")
		//startTime1, _ := time.ParseInLocation("2006-01-02", beginTime, Loc)
		//endTime = endTime + " 23:59:59"
		//endTime1, _ := time.ParseInLocation(constants.TimeFormat, endTime, Loc)
		startTime1, endTime1 := utils2.GetBeginAndEndTime(beginTime, endTime)
		db.Where("`sys_role`.create_time >= ?", startTime1)
		db.Where("`sys_role`.create_time <= ?", endTime1)
	}
	db.Order("`sys_role`.role_sort")

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

// 添加权限管理用户
func AddRolesByUser(user SysUserParm) {
	roleIds := user.RoleIds
	userId := user.UserId
	InsertRolesByUser(userId, roleIds)
}

func InsertRolesByUser(userId int, roleIds []int) R.Result {
	var roless []SysUserRole
	for i := 0; i < len(roleIds); i++ {
		var roles = SysUserRole{
			UserId: userId,
			RoleId: roleIds[i],
		}
		roless = append(roless, roles)
	}
	err := mysql.MysqlDb().Create(&roless).Error
	if err != nil {
		panic(R.ReturnFailMsg("添加权限管理用户失败"))
	}
	return R.ReturnSuccess("操作成功")
}

// 添加权限管理用户
func DeleteRolesByUser(userId []int) {
	err := mysql.MysqlDb().Exec("delete from sys_role_actor where aid in (?)", userId).Error
	if err != nil {
		panic(R.ReturnFailMsg("删除权限关联用户失败"))
	}
}

// 批量删除角色信息
func DeleteRolesById(roleId string, userId int) {
	roleIds := utils2.Split(roleId)
	for i := 0; i < len(roleIds); i++ {
		roleId := roleIds[i]
		roleIdStr := strconv.Itoa(roleId)
		//校验角色是否允许操作
		checkRoleAllowed(roleIdStr)
		//校验角色是否有数据权限
		checkRoleDataScope(roleIdStr, userId)
		role := FindRoleInfoById(roleIdStr)
		if countUserRoleByRoleId(roleIdStr) > 0 {
			panic(R.ReturnFailMsg(role.RoleName + "已分配,不能删除"))
		}
	}
	//删除角色与菜单关联
	DeleteRoleMenu(roleId)

	err := mysql.MysqlDb().Exec("update sys_role set avtag = 0 where id in (" + roleId + ")").Error
	if err != nil {
		panic(R.ReturnFailMsg("删除权限关联用户失败"))
	}
}

func FindRoleInfoById(roleId string) SysRoles {
	var role SysRoles
	err := mysql.MysqlDb().Where("id = ?", roleId).First(&role).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return role
}

// 校验角色是否有数据权限
func CheckRoleDataScope(roleId string) bool {
	var sql = baseSql + "where 1=1 AND r.id = " + roleId + " "
	sql += "order by r.ornum"
	var count int64
	err := mysql.MysqlDb().Raw(sql).Count(&count).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return count < 1
}

// 校验角色名称是否存在
func checkRoleNameUnique(roleName string) SysRoles {
	var role SysRoles
	var sql = baseSql + "where r.name = '" + roleName + "' limit 1"
	err := mysql.MysqlDb().Raw(sql).Scan(&role).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return role
}

// 校验角色key是否存在
func checkRoleKeyUnique(roleKey string) SysRoles {
	var role SysRoles
	_ = roleKey
	// dump 的 sys_role 无 role_key 列，不做 key 唯一性校验
	return role
}

// 校验角色是否允许操作
func checkRoleAllowed(roleId string) {
	if roleId != "" && "1" == roleId {
		panic(R.ReturnFailMsg("不允许操作超级管理员角色"))
	}
}

func countUserRoleByRoleId(roleId string) int {
	sql := "select count(1) from sys_role_actor where rid=" + roleId
	var count int
	err := mysql.MysqlDb().Raw(sql).Scan(&count).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return count
}

// 校验角色是否有数据权限
func checkRoleDataScope(roleId string, userId int) {
	if !IsAdminById(utils2.GetInterfaceToInt(userId)) {
		var sql = baseSql + "where 1=1 AND r.id = " + roleId + " " + "order by r.ornum"
		var list []SysRoles
		err := mysql.MysqlDb().Raw(sql).Scan(&list).Error
		if err != nil {
			panic(R.ReturnFailMsg(err.Error()))
		}
		if len(list) < 1 {
			panic(R.ReturnFailMsg("没有权限访问角色数据！"))
		}
	}
}

const baseSql = "select distinct r.id, r.name, r.ornum, r.scope, " +
	"r.avtag, r.crtim, r.notes " +
	"from sys_role r " +
	"left join sys_role_actor ur on ur.rid = r.id " +
	"left join sys_user u on u.id = ur.aid " +
	"left join sys_org d on u.orgid = d.id "

func SaveRole(roles SysRolesParam) R.Result {
	/*角色名称已存在*/
	roleName := roles.RoleName
	var role = checkRoleNameUnique(roleName)
	if role.RoleId != 0 {
		return R.ReturnFailMsg("新增角色'" + role.RoleName + "'失败，角色名称已存在")
	}
	/*角色权限已存在*/
	roleKey := roles.RoleKey
	role = checkRoleKeyUnique(roleKey)
	if role.RoleId != 0 {
		return R.ReturnFailMsg("新增角色'" + role.RoleName + "'失败，角色权限已存在")
	}
	//数据范围（1：全部数据权限 2：自定数据权限 3：本部门数据权限 4：本部门及以下数据权限）
	roles.DataScope = "2"
	roles.DelFlag = "0"
	err := mysql.MysqlDb().Model(&SysRoles{}).Create(&roles).Error
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	insertRoleMenu(roles)
	return R.ReturnSuccess("操作成功")
}

func insertRoleMenu(roles SysRolesParam) {
	menuIds := roles.MenuIds
	if menuIds == nil || len(menuIds) == 0 {
		return
	}
	var roleMenu []SysRoleMenu
	for i := 0; i < len(menuIds); i++ {
		menuId := menuIds[i]
		roleId := roles.RoleId
		roleMenu = append(roleMenu, SysRoleMenu{roleId, menuId})
	}
	err := mysql.MysqlDb().Model(&SysRoleMenu{}).Create(&roleMenu).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
}

/*更新*/
func UploadRole(rolesParam SysRolesParam, userId int) R.Result {
	//校验角色是否允许操作
	checkRoleAllowed(strconv.Itoa(rolesParam.RoleId))
	/*校验角色是否有数据权限*/
	checkRoleDataScope(strconv.Itoa(rolesParam.RoleId), userId)
	/*角色名称已存在*/
	roleName := rolesParam.RoleName
	var role = checkRoleNameUnique(roleName)
	if role.RoleId != 0 && rolesParam.RoleId != role.RoleId {
		return R.ReturnFailMsg("新增角色'" + role.RoleName + "'失败，角色名称已存在")
	}
	/*角色权限已存在*/
	roleKey := rolesParam.RoleKey
	role = checkRoleKeyUnique(roleKey)
	if role.RoleId != 0 && rolesParam.RoleId != role.RoleId {
		return R.ReturnFailMsg("新增角色'" + role.RoleName + "'失败，角色权限已存在")
	}

	var roles SysRoles
	err := copier.Copy(&roles, rolesParam)
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}

	err = mysql.MysqlDb().Model(&SysRoles{}).
		Where("rid = ?", roles.RoleId).
		Updates(&roles).Error
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	// 删除角色与菜单关联
	DeleteRoleMenuByRoleId(strconv.Itoa(rolesParam.RoleId))
	//新增角色菜单信息
	insertRoleMenu(rolesParam)
	// 更新缓存用户权限
	return R.ReturnSuccess("操作成功")
}

func PutDataScope(rolesParam SysRolesParam, userId int) R.Result {
	/*校验角色是否允许操作*/
	checkRoleAllowed(strconv.Itoa(rolesParam.RoleId))
	/*校验角色是否有数据权限*/
	checkRoleDataScope(strconv.Itoa(rolesParam.RoleId), userId)
	/*修改角色信息*/
	err := mysql.MysqlDb().Model(&SysRoles{}).Where("id", rolesParam.RoleId).Updates(&rolesParam).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess("操作成功")
}

func ChangeRoleStatus(rolesParam SysRoles, userId int) R.Result {
	/*校验角色是否允许操作*/
	checkRoleAllowed(strconv.Itoa(rolesParam.RoleId))
	/*校验角色是否有数据权限*/
	checkRoleDataScope(strconv.Itoa(rolesParam.RoleId), userId)
	err := mysql.MysqlDb().Updates(&rolesParam).Error
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}

func GetRoleOptionSelect() R.Result {
	var sql = baseSql + "where 1=1"
	sql += "order by r.ornum"
	var rols []SysRoles
	err := mysql.MysqlDb().Raw(sql).Scan(&rols).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess(rols)
}

func GetAllocatedList(params tools.SearchTableDataParam) tools.TableDataInfo {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysUser := params.Other.(SysUserParm)
	offset := (pageNum - 1) * pageSize
	var total int64
	var rows []SysUser

	sql := "select distinct u.* " +
		"from sys_user u left join sys_org d on u.orgid = d.id " +
		"left join sys_role_actor ur on u.id = ur.aid " +
		"left join sys_role r on r.id = ur.rid " +
		"where r.id = " + strconv.Itoa(sysUser.RoleId)

	var userNmae = sysUser.UserName
	if userNmae != "" {
		sql += "AND u.username like concat('%', " + userNmae + ", '%')"
	}
	var phonenumber = sysUser.Phonenumber
	if phonenumber != "" {
		sql += "AND u.phonenumber like concat('%', " + phonenumber + ", '%')"
	}
	var beginTime = params.Params.BeginTime
	var endTime = params.Params.EndTime

	if beginTime != "" {
		startTime1, endTime1 := utils2.GetBeginAndEndTime(beginTime, endTime)
		sql += "u.create_time >= " + startTime1.String()
		sql += "u.create_time <= " + endTime1.String()
	}
	var db = mysql.MysqlDb().Model(&rows)
	if err := db.Count(&total).Error; err != nil {
		return tools.Fail()
	}

	if err := db.Raw(sql).Limit(pageSize).Offset(offset).Find(&rows).Error; err != nil {
		return tools.Fail()
	}

	if rows == nil {
		return tools.Fail()
	} else {
		return tools.Success(rows, total)
	}
}

func GetUnAllocatedList(params tools.SearchTableDataParam) tools.TableDataInfo {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysUser := params.Other.(SysUserParm)
	offset := (pageNum - 1) * pageSize
	var total int64
	var rows []SysUser

	sql := "select distinct u.* " +
		"from sys_user u left join sys_org d on u.orgid = d.id " +
		"left join sys_role_actor ur on u.id = ur.aid " +
		"left join sys_role r on r.id = ur.rid " +
		"where (r.id != " + strconv.Itoa(sysUser.RoleId) + " or r.id IS NULL) " +
		"and u.id not in (select u.id from sys_user u inner join sys_role_actor ur on u.id = ur.aid and ur.rid = " + strconv.Itoa(sysUser.RoleId) + ") "

	var userNmae = sysUser.UserName
	if userNmae != "" {
		sql += "AND u.username like concat('%', " + userNmae + ", '%')"
	}
	var phonenumber = sysUser.Phonenumber
	if phonenumber != "" {
		sql += "AND u.phonenumber like concat('%', " + phonenumber + ", '%')"
	}
	var beginTime = params.Params.BeginTime
	var endTime = params.Params.EndTime

	if beginTime != "" {
		startTime1, endTime1 := utils2.GetBeginAndEndTime(beginTime, endTime)
		sql += "u.create_time >= " + startTime1.String()
		sql += "u.create_time <= " + endTime1.String()
	}
	var db = mysql.MysqlDb().Model(&rows)
	if err := db.Count(&total).Error; err != nil {
		return tools.Fail()
	}

	if err := db.Raw(sql).Limit(pageSize).Offset(offset).Find(&rows).Error; err != nil {
		return tools.Fail()
	}

	if rows == nil {
		return tools.Fail()
	} else {
		return tools.Success(rows, total)
	}
}

func CancelRole(userId int, roleId int) R.Result {
	err := mysql.MysqlDb().Exec("delete from sys_role_actor where aid = ? and rid = ?", userId, roleId).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess("操作成功")
}

func CancelAllRole(roleId string, userIds string) R.Result {
	sql := "delete from sys_role_actor where rid=" + roleId + " and aid in ( " + userIds + " )"
	err := mysql.MysqlDb().Exec(sql).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess("操作成功")
}

func SelectRoleAll(roleId string, userIdStr string, userId int) R.Result {
	checkRoleDataScope(roleId, userId)
	/*批量插入*/
	var userRoles []SysUserRole
	var userIds = utils2.Split(userIdStr)
	for i := 0; i < len(userIds); i++ {
		id := userIds[i]
		userRoles = append(userRoles, SysUserRole{RoleId: utils2.GetInterfaceToInt(roleId), UserId: id})
	}
	err := mysql.MysqlDb().Model(&SysUserRole{}).Create(&userRoles).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess("操作成功")
}
