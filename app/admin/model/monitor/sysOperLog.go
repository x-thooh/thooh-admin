package monitor

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/x-thooh/thooh-admin/app/admin/model/system"
	"github.com/x-thooh/thooh-admin/app/admin/model/tools"
	utils2 "github.com/x-thooh/thooh-admin/app/core/utils"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

// SysOperLog model：数据库字段
type SysOperLog struct {
	OperId        int       `json:"operId" gorm:"column:id;primaryKey"` //表示主键
	Title         string    `json:"title" gorm:"column:opmod"`
	BusinessType  string    `json:"businessType" gorm:"column:butyp"`
	Method        string    `json:"method" gorm:"column:remet"`
	RequestMethod string    `json:"requestMethod" gorm:"column:reway"`
	OperatorType  string    `json:"operatorType" gorm:"column:optyp"`
	OperName      string    `json:"operName" gorm:"column:opuna"`
	DeptName      string    `json:"deptName" gorm:"column:opdna"`
	OperUrl       string    `json:"operUrl" gorm:"column:reurl"`
	OperIp        string    `json:"operIp" gorm:"column:opip"`
	OperLocation  string    `json:"operLocation" gorm:"column:oploc"`
	OperParam     string    `json:"operParam" gorm:"column:bapar"`
	JsonResult    string    `json:"jsonResult" gorm:"column:repar"`
	Status        string    `json:"status" gorm:"column:sutag"`
	ErrorMsg      string    `json:"errorMsg" gorm:"column:ermsg"`
	OperTime      time.Time `json:"operTime" gorm:"column:optim;type:datetime;autoCreateTime"`
}

// 表中的状态值
const (
	BusinessTypeOther = "0"
	BusinessTypeAdd   = "1"
	BusinessTypeEdit  = "2"
	BusinessTypeDel   = "3"

	OperatorTypeOther = "0"
	OperatorTypeAdmin = "1"
	OperatorTypePhone = "2"
)

// TableName 指定数据库表名称
func (SysOperLog) TableName() string {
	return "mon_oper_log"
}

func SelectOperLogList(params tools.SearchTableDataParam) tools.TableDataInfo {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	offset := (pageNum - 1) * pageSize

	sysOperLog := params.Other.(SysOperLog)

	var rows []SysOperLog

	var beginTime = params.Params.BeginTime
	var endTime = params.Params.EndTime

	var total int64
	var db = mysql.MysqlDb().Model(&rows)

	var title = sysOperLog.Title
	if title != "" {
		db.Where("title like concat('%', ?, '%')", title)
	}
	var businessType = sysOperLog.BusinessType
	if businessType != "" {
		db.Where("butyp = ?", businessType)
	}

	/*目前没有用*/
	//var businessTypes = sysOperLog.BusinessTypes
	//if businessTypes != nil || len(businessTypes) > 0 {
	//	//db.Table("users").Where("id in ? ",[]int{1,2,3}).Find(&user)
	//	db.Where("business_type in ?", businessTypes)
	//}

	var status = sysOperLog.Status
	if status != "" {
		db.Where("status = ?", status)
	}

	var oper_name = sysOperLog.OperName
	if oper_name != "" {
		db.Where("opuna like concat('%', ?, '%')", oper_name)
	}
	var orderByColumn = params.OrderByColumn
	var isAsc = params.IsAsc

	if orderByColumn != "" {
		if "ascending" == isAsc {
			if "operTime" == orderByColumn {
				db.Order("optim DESC")
			}
			if "operName" == orderByColumn {
				db.Order("opuna DESC")
			}
		}
		if "descending" == isAsc {
			if "operTime" == orderByColumn {
				db.Order("optim ASC")
			}
			if "operName" == orderByColumn {
				db.Order("opuna ASC")
			}
		}
	}

	if beginTime != "" {
		//Loc, _ := time.LoadLocation("Asia/Shanghai")
		//startTime1, _ := time.ParseInLocation(constants.DateFormat, beginTime, Loc)
		//endTime = endTime + " 23:59:59"
		//endTime1, _ := time.ParseInLocation(constants.DateFormat, endTime, Loc)
		startTime1, endTime1 := utils2.GetBeginAndEndTime(beginTime, endTime)
		//db.Where("optim >= ? and optim <= ?", startTime1, endTime1)
		db.Where("optim >= ?", startTime1)
		db.Where("optim <= ?", endTime1)
	}

	db.Order("id desc")
	if err := db.Table(sysOperLog.TableName()).Count(&total).Error; err != nil {
		return tools.Fail()
	}
	if err := db.Limit(pageSize).Offset(offset).Find(&rows).Error; err != nil {
		return tools.Fail()
	}

	if rows == nil {
		return tools.Fail()
	} else {
		return tools.Success(rows, total)
	}
}

func DelectOperlog(operIds []int) R.Result {
	if err := mysql.MysqlDb().Where("id in (?)", operIds).Delete(&SysOperLog{}).Error; err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}

func ClearOperlog() R.Result {
	if err := mysql.MysqlDb().Exec("truncate table mon_oper_log").Error; err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}

func (param *SysOperLog) OperationLogAdd(context *gin.Context) R.Result {
	userId, _ := context.Get("userId")
	if userId != nil {
		sysUser := system.FindUserById(userId)
		dept := system.GetDeptInfo(strconv.Itoa(sysUser.DeptId))
		param.OperName = sysUser.UserName
		param.DeptName = dept.DeptName
		param.OperatorType = "1"
	}

	ip := utils2.GetRemoteClientIp(context.Request)
	method := context.Request.Method
	param.Method = method
	param.RequestMethod = method

	if method == "GET" {
		param.BusinessType = BusinessTypeOther
	}
	if method == "POST" {
		param.BusinessType = BusinessTypeAdd
	}
	if method == "DEL" {
		param.BusinessType = BusinessTypeDel
	}
	if method == "PUT" {
		param.BusinessType = BusinessTypeEdit
	}

	param.OperUrl = context.Request.URL.Path

	param.OperIp = ip
	param.OperTime = time.Now()
	param.OperLocation = "" + utils2.GetRealAddressByIP(ip)
	if err := mysql.MysqlDb().Model(&SysOperLog{}).Create(&param).Error; err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}
