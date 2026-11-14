package system

import (
	"fmt"
	"strconv"
	"time"

	"github.com/x-thooh/thooh-admin/app/admin/model/constants"
	"github.com/x-thooh/thooh-admin/app/admin/model/tools"
	utils2 "github.com/x-thooh/thooh-admin/app/core/utils"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/common/json/boolx"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

// SysUser model：数据库字段
type SysUser struct {
	UserId       string     `json:"userId" gorm:"column:id;primaryKey"` //表示主键
	DeptId       string     `json:"deptId" gorm:"column:orgid"`
	UserName     string     `json:"userName" gorm:"column:username"`
	NickName     string     `json:"nickName" gorm:"column:name"`
	UserType     string     `json:"userType" gorm:"column:type"`
	Email        string     `json:"email" gorm:"column:email"`
	Phonenumber  string     `json:"phonenumber" gorm:"column:monum"`
	Sex          string     `json:"sex" gorm:"column:gender"`
	Avatar       string     `json:"avatar" gorm:"column:avatar"`
	Password     string     `json:"password" gorm:"column:password"`
	Status       boolx.Bool `json:"status" gorm:"column:avtag"` // WHY: avtag 是 bit(1)，boolx 有 Scan/Value
	StatusFilter string     `json:"-" gorm:"-"`                 // 检索用的三态："" 不过滤、"0" 正常、"1" 停用
	DelFlag      string     `json:"delFlag" gorm:"-"`
	LoginIp      string     `json:"loginIp" gorm:"column:loip"`
	LoginDate    time.Time  `json:"loginDate" gorm:"column:lotim;type:datetime"`
	CreateBy     string     `json:"createBy" gorm:"-"`
	CreateTime   time.Time  `json:"createTime" gorm:"column:crtim;type:datetime;autoCreateTime"`
	UpdateBy     string     `json:"updateBy" gorm:"-"`
	UpdateTime   time.Time  `json:"updateTime" gorm:"column:uptim;type:datetime;autoCreateTime"`
	Remark       string     `json:"remark" gorm:"column:notes"`
}

type SysUserParm struct {
	UserId      string    `json:"userId" gorm:"column:id;primaryKey"` //表示主键
	DeptId      string    `json:"deptId" gorm:"column:orgid"`
	UserName    string    `json:"userName" gorm:"column:username"`
	NickName    string    `json:"nickName" gorm:"column:name"`
	UserType    string    `json:"userType" gorm:"column:type"`
	Email       string    `json:"email" gorm:"column:email"`
	Phonenumber string    `json:"phonenumber" gorm:"column:monum"`
	Sex         string    `json:"sex" gorm:"column:gender"`
	Avatar      string    `json:"avatar" gorm:"column:avatar"`
	Password    string    `json:"password" gorm:"column:password"`
	Status      string    `json:"status" gorm:"column:avtag"` // 请求/导出口径，RuoYi 的 0=正常
	DelFlag     string    `json:"delFlag" gorm:"-"`
	LoginIp     string    `json:"loginIp" gorm:"column:loip"`
	LoginDate   string    `json:"loginDate" gorm:"column:lotim;type:datetime"`
	Remark      string    `json:"remark" gorm:"column:notes"`
	CreateBy    string    `json:"createBy" gorm:"-"`
	CreateTime  time.Time `json:"createTime" gorm:"column:crtim;type:datetime"`
	UpdateBy    string    `json:"updateBy" gorm:"-"`
	UpdateTime  time.Time `json:"updateTime" gorm:"column:uptim;type:datetime"`
	DeptName    string    `json:"deptName,omitempty"`
	Leader      string    `json:"leader,omitempty"`
	PostIds     []string  `json:"postIds,omitempty"`
	RoleIds     []int     `json:"roleIds,omitempty"`
	RoleId      int       `json:"roleId,omitempty"`
}

type SysUserExcel struct {
	UserId      string    `json:"userId" gorm:"column:id;primaryKey"` //表示主键
	DeptId      string    `json:"deptId" gorm:"column:orgid"`
	UserName    string    `json:"userName" gorm:"column:username"`
	NickName    string    `json:"nickName" gorm:"column:name"`
	UserType    string    `json:"userType" gorm:"column:type"`
	Email       string    `json:"email" gorm:"column:email"`
	Phonenumber string    `json:"phonenumber" gorm:"column:monum"`
	Sex         string    `json:"sex" gorm:"column:gender"`
	Avatar      string    `json:"avatar" gorm:"column:avatar"`
	Password    string    `json:"password" gorm:"column:password"`
	Status      string    `json:"status" gorm:"column:avtag"` // 请求/导出口径，RuoYi 的 0=正常
	DelFlag     string    `json:"delFlag" gorm:"-"`
	LoginIp     string    `json:"loginIp" gorm:"column:loip"`
	LoginDate   time.Time `json:"loginDate" gorm:"column:lotim;type:datetime"`
	CreateBy    string    `json:"createBy" gorm:"-"`
	CreateTime  time.Time `json:"createTime" gorm:"column:crtim;type:datetime"`
	UpdateBy    string    `json:"updateBy" gorm:"-"`
	UpdateTime  time.Time `json:"updateTime" gorm:"column:uptim;type:datetime"`
	Remark      string    `json:"remark" gorm:"column:notes"`
	DeptName    string    `json:"deptName,omitempty"`
	Leader      string    `json:"leader,omitempty"`
}

// LoginParam 登录参数
type LoginParam struct {
	Code     string `json:"code"`
	Password string `json:"password"`
	UserName string `json:"username"`
	Uuid     string `json:"uuid"`
}

// Userparam 请求参数
type Userparam struct {
	NickName    string `json:"nickName"`
	UserName    string `json:"userName"`
	Phonenumber string `json:"phonenumber"`
	Email       string `json:"email" binding:"email" msg:"邮箱地址格式不正确"`
	Sex         string `json:"sex"`
}

// TableName 指定数据库表名称
func (SysUser) TableName() string {
	return "sys_user"
}

// IsAdmin 指定数据库表名称
func IsAdmin(user *SysUser) bool {
	return user.UserId == "u1"
}

// IsAdmin 指定数据库表名称
func IsAdminById(userId string) bool {
	return userId == "u1"
}

// IsExistUser 判断用户是否存在 返回bool类型
func IsExistUser(loginName string) bool {
	var user SysUser
	err := mysql.MysqlDb().Where("username = ?", loginName).First(&user).Error
	if err != nil {
		return false
	}
	return true
}

func IsExistUserByPhoneNumber(phonenumber string) bool {
	var user SysUser
	err := mysql.MysqlDb().Where("monum = ?", phonenumber).First(&user).Error
	if err != nil {
		return false
	}
	return true
}

func IsExistUserByEmail(email string) bool {
	var user SysUser
	err := mysql.MysqlDb().Where("email = ?", email).First(&user).Error
	if err != nil {
		return false
	}
	return true
}

// 登录用到
func FindUserByName(loginName string) SysUser {
	var user SysUser
	err := mysql.MysqlDb().Where("username = ?", loginName).Find(&user).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return user
}

func FindUserById(id any) SysUser {
	var user SysUser
	var db = mysql.MysqlDb().Model(&user).
		Select("`sys_user`.*, d.name as dept_name, d.label as leader").
		Joins("left join sys_org d on d.id = `sys_user`.orgid")
	err := db.Where("`sys_user`.id = ?", fmt.Sprint(id)).First(&user).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	user.Password = ""
	return user
}

// 查找用户密码
func FindUserPassWordById(id any) string {
	var user SysUser
	var db = mysql.MysqlDb().Model(&user).
		Select("`sys_user`.*")
	err := db.Where("`sys_user`.id = ?", fmt.Sprint(id)).First(&user).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return user.Password
}

// 更新用户密码
func UploadUserPassWord(id any, password string) {
	userId := utils2.GetInterfaceToInt(id)
	err := mysql.MysqlDb().Exec("update sys_user set password = ? where id = ?", password, userId).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
}

/*校验用户是否有数据权限*/
func CheckUserDataScope(userId string, useridP string) {
	if !IsAdminById(userId) {
		var param = tools.SearchTableDataParam{
			Other: SysUser{
				UserId: useridP,
			},
		}
		var row = SelectUserList(param, false)
		if row.Rows == nil {
			panic(R.ReturnFailMsg("没有权限访问用户数据！"))
		}
	}
}

func SelectUserList(params tools.SearchTableDataParam, isPage bool) tools.TableDataInfo {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysUser := params.Other.(SysUser)

	offset := (pageNum - 1) * pageSize
	var total int64
	var rows []SysUser

	var db = mysql.MysqlDb().Model(&rows).
		Select("`sys_user`.*, d.name as dept_name, d.label as leader").
		Joins("left join sys_org d on d.id = `sys_user`.orgid")

	var userId = sysUser.UserId
	if userId != "" {
		db.Where("`sys_user`.id = ?", userId)
	}
	var deptId = sysUser.DeptId
	if deptId != "" {
		db.Where("`sys_user`.orgid = ? OR `sys_user`.orgid IN (SELECT t.id FROM sys_org t WHERE find_in_set(?, t.tier))", deptId, deptId)
	}

	var userName = sysUser.UserName
	if userName != "" {
		db.Where("`sys_user`.username like concat('%', ?, '%')", userName)
	}

	// WHY: DeleteUserById 把行写成 avtag=0（dump 没有单独的 del_flag 列），
	// 所以「已删除」和「已停用」在这张表里共用 avtag 这一位；列表常驻只出 avtag=1，
	// 否则删掉的账号还会留在列表里（审计实测：删除后 total 仍为 10）。
	db.Where("`sys_user`.avtag = 1")

	var phonenumber = sysUser.Phonenumber
	if phonenumber != "" {
		db.Where("`sys_user`.monum = ? ", phonenumber)
	}
	var beginTime = params.Params.BeginTime
	var endTime = params.Params.EndTime

	if beginTime != "" {
		startTime1, endTime1 := utils2.GetBeginAndEndTime(beginTime, endTime)
		db.Where("`sys_user`.crtim >= ?", startTime1)
		db.Where("`sys_user`.crtim <= ?", endTime1)
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

func SelectUserParmList(params tools.SearchTableDataParam, isPage bool) tools.TableDataInfo {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysUser := params.Other.(SysUser)

	offset := (pageNum - 1) * pageSize
	var total int64
	var rows []SysUserExcel

	var db = mysql.MysqlDb().Model(&rows).
		Select("`sys_user`.*, d.name as dept_name, d.label as leader").
		Joins("left join sys_org d on d.id = `sys_user`.orgid")

	var userId = sysUser.UserId
	if userId != "" {
		db.Where("`sys_user`.id = ?", userId)
	}
	var deptId = sysUser.DeptId
	if deptId != "" {
		db.Where("`sys_user`.orgid = ? OR `sys_user`.orgid IN (SELECT t.id FROM sys_org t WHERE find_in_set(?, t.tier))", deptId, deptId)
	}

	var userName = sysUser.UserName
	if userName != "" {
		db.Where("`sys_user`.username like concat('%', ?, '%')", userName)
	}

	// WHY: DeleteUserById 把行写成 avtag=0（dump 没有单独的 del_flag 列），
	// 所以「已删除」和「已停用」在这张表里共用 avtag 这一位；列表常驻只出 avtag=1，
	// 否则删掉的账号还会留在列表里（审计实测：删除后 total 仍为 10）。
	db.Where("`sys_user`.avtag = 1")

	var phonenumber = sysUser.Phonenumber
	if phonenumber != "" {
		db.Where("`sys_user`.monum = ? ", phonenumber)
	}
	var beginTime = params.Params.BeginTime
	var endTime = params.Params.EndTime

	if beginTime != "" {
		startTime1, endTime1 := utils2.GetBeginAndEndTime(beginTime, endTime)
		db.Where("`sys_user`.crtim >= ?", startTime1)
		db.Where("`sys_user`.crtim <= ?", endTime1)
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

func GetUserDeptTree() []SysDeptDto {

	var param = tools.SearchTableDataParam{
		Other: SysDept{},
	}

	var result, total = GetDeptList(param, false)
	var data []SysDeptDto
	for i := 0; i < int(total); i++ {
		var bean = result[i]
		if bean.ParentId == "" {
			dept := SysDeptDto{
				Id:    bean.DeptId,
				Label: bean.DeptName,
			}
			data = append(data, getDeptChildren(result, dept))
		}
	}

	return data
}

func getDeptChildren(list []SysDeptResult, dept SysDeptDto) SysDeptDto {
	var data []SysDeptDto
	for i := 0; i < len(list); i++ {
		var bean = list[i]
		if bean.ParentId == dept.Id {
			dept := SysDeptDto{
				Id:    bean.DeptId,
				Label: bean.DeptName,
			}
			data = append(data, getDeptChildren(list, dept))
		}
	}
	dept.Children = data
	return dept
}

func ImportUserData(users []SysUserParm, updateSupport string) (string, string) {
	var errList []string
	var error string
	for i := 0; i < len(users); i++ {
		var u1 = users[i]
		u1.CreateTime = time.Now()
		var userName = u1.UserName
		var u2 = FindUserByName(userName)

		password := SelectConfigByKey("sys.user.initPassword")
		var pwd = ""
		if password != "" {
			pwd, _ = utils2.PasswordHash(password)
		} else {
			pwd, _ = utils2.PasswordHash("123456")
		}

		u1.Password = pwd
		var d = strconv.Itoa(i + 1)
		if u2.UserId == "" {
			err := SaveUser(u1)
			if err != "" {
				error = "error"
				errList = append(errList, d+"、用户名："+userName+"，添加失败<br/>")
			} else {
				errList = append(errList, d+"、用户名："+userName+"，添加成功<br/>")
			}
		} else {
			if updateSupport == "true" {
				userIds := make([]string, 0)
				userIds = append(userIds, u2.UserId)
				DeleteUser(userIds)
				err := SaveUser(u1)
				if err != "" {
					error = "error"
					errList = append(errList, d+"、用户名："+userName+"，添加失败<br/>")
				} else {
					errList = append(errList, d+"、用户名："+userName+"，添加成功<br/>")
				}
			} else {
				error = "error"
				errList = append(errList, d+"、用户名："+userName+"，已存在<br/>")
			}
		}
	}
	var result string
	for _, i := range errList {
		result += i
	}
	return error, result
}

func SaveUser(user SysUserParm) string {
	var result = ""
	var u = SysUser{
		UserId:      newUserId(), // WHY: sys_user.id 是 varchar(36)，前端表单不带主键，必须后端生成
		NickName:    user.NickName,
		DeptId:      user.DeptId,
		UserName:    user.UserName,
		UserType:    "00",
		Email:       user.Email,
		Phonenumber: user.Phonenumber,
		Sex:         user.Sex,
		Avatar:      user.Avatar,
		Password:    user.Password,
		LoginDate:   user.CreateTime,
		Status:      true,
		DelFlag:     "0",
		CreateBy:    user.CreateBy,
		CreateTime:  user.CreateTime,
		UpdateTime:  user.CreateTime,
		Remark:      user.Remark,
	}
	err1 := mysql.MysqlDb().Model(&SysUser{}).Create(&u).Error
	if err1 != nil {
		result = "" + err1.Error()
	}
	user.UserId = u.UserId
	AddPostByUser(user)
	AddRolesByUser(user)
	return result
}

func UploadUser(userParm SysUserParm) {
	var userIds = []string{userParm.UserId}
	DeleteRolesByUser(userIds)
	AddRolesByUser(userParm)
	DeletePostByUser(userIds)
	AddPostByUser(userParm)
	var user = SysUser{
		UserId:      userParm.UserId,
		DeptId:      userParm.DeptId,
		NickName:    userParm.NickName,
		Phonenumber: userParm.Phonenumber,
		Email:       userParm.Email,
		Sex:         userParm.Sex,
		Status:      boolx.Bool(userParm.Status == "0"),
		Remark:      userParm.Remark,
	}
	err := mysql.MysqlDb().Updates(&user).Error
	if err != nil {
		panic(R.ReturnFailMsg("更新信息失败"))
	}
}

func EditProfileUserInfo(userId string, param Userparam) R.Result {
	var user SysUser
	err1 := mysql.MysqlDb().Where("id = ?", userId).First(&user)

	if err1.Error != nil {
		return R.ReturnFailMsg("未找到用户")
	}

	data := make(map[string]interface{})

	if param.NickName != "" {
		data["nick_name"] = param.NickName
	}

	if param.Email != "" {
		data["email"] = param.Email
	}

	if param.Phonenumber != "" {
		data["phonenumber"] = param.Phonenumber
	}

	if param.Sex != "" {
		data["sex"] = param.Sex
	}
	//等价于: UPDATE `foods` SET `price` = '35', `stock` = '0'  WHERE (user_id = '2')
	err2 := mysql.MysqlDb().Model(&SysUser{}).Where("id = ?", userId).Updates(data)

	if err2.Error != nil {
		return R.ReturnFailMsg("修改失败")
	}

	return R.ReturnSuccess("修改成功")
}

func DeleteUser(userId []string) R.Result {
	for _, v := range userId {
		if v == constants.AdminId {
			return R.ReturnFailMsg("管理员数据不开操作")
		}
	}
	// 删除部门管理
	DeletePostByUser(userId)
	// 删除角色管理
	DeleteRolesByUser(userId)
	// 删除用户
	DeleteUserById(userId)
	return R.ReturnSuccess("操作成功")
}

func DeleteUserById(userId []string) R.Result {
	err := mysql.MysqlDb().Exec("update sys_user set avtag = 0 where id in (?) ", userId).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess("操作成功")
}

func ChangeUserStatus(param SysUserParm) R.Result {
	data := make(map[string]interface{})

	if param.Status != "" {
		avtag := 0
		if param.Status == "0" {
			avtag = 1
		}
		data["avtag"] = avtag // WHY: 列名是 avtag；RuoYi 的 0=正常 对应 avtag 1
	}

	//等价于: UPDATE `foods` SET `price` = '35', `stock` = '0'  WHERE (user_id = '2')
	err2 := mysql.MysqlDb().Model(&SysUser{}).Where("id = ?", param.UserId).Updates(data)
	if err2.Error != nil {
		return R.ReturnFailMsg("修改失败")
	}

	return R.ReturnSuccess("修改成功")
}

func ResetPwd(param SysUserParm) R.Result {
	data := make(map[string]interface{})

	if param.Password != "" {
		var pwd, _ = utils2.PasswordHash(param.Password)
		data["password"] = pwd
	}

	//等价于: UPDATE `foods` SET `price` = '35', `stock` = '0'  WHERE (user_id = '2')
	err2 := mysql.MysqlDb().Model(&SysUser{}).Where("id = ?", param.UserId).Updates(data)
	if err2.Error != nil {
		return R.ReturnFailMsg("修改失败")
	}

	return R.ReturnSuccess("修改成功")
}

// newUserId 造一个 varchar(36) 用户主键。
// WHY: dump 的 sys_user.id 是 varchar(36)（u1/u2…），新增接口的表单没有主键字段，
// 不自增就会插进空串（浏览器新增用户实测：id=” 直接违反主键约定）。
func newUserId() string {
	return "u" + strconv.FormatInt(time.Now().UnixNano(), 36)
}
