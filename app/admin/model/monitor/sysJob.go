package monitor

import (
	"github.com/x-thooh/thooh-admin/common/json/bitx"
	"time"

	"github.com/jinzhu/copier"
	"github.com/x-thooh/thooh-admin/app/admin/model/system"
	"github.com/x-thooh/thooh-admin/app/admin/model/tools"
	utils2 "github.com/x-thooh/thooh-admin/app/core/utils"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

type SysJobParam struct {
	JobId          int
	Concurrent     string
	CronExpression string
	InvokeTarget   string
	JobGroup       string
	JobName        string
	MisfirePolicy  string
	Status         string
}
type SysJob struct {
	JobId          int       `json:"jobId" gorm:"column:id;primaryKey"` //表示主键
	JobName        string    `json:"jobName" gorm:"column:name"`
	JobGroup       string    `json:"jobGroup" gorm:"-"` // dump 无此列
	InvokeTarget   string    `json:"invokeTarget" gorm:"column:code"`
	CronExpression string    `json:"cronExpression" gorm:"column:cron"`
	MisfirePolicy  int       `json:"misfirePolicy" gorm:"column:retyp"`
	Concurrent     int       `json:"concurrent" gorm:"-"` // dump 无此列
	Status         bitx.Str  `json:"status" gorm:"column:avtag"`
	CreateBy       string    `json:"createBy" gorm:"-"` // dump 无此列
	CreateTime     time.Time `json:"createTime" gorm:"column:crtim;type:datetime"`
	UpdateBy       string    `json:"updateBy" gorm:"-"`   // dump 无此列
	UpdateTime     time.Time `json:"updateTime" gorm:"-"` // dump 无此列
	Remark         string    `json:"remark" gorm:"column:notes"`
}

// TableName 指定数据库表名称
func (SysJob) TableName() string {
	return "mon_job"
}

type SysJobLog struct {
	JobLogId      int       `json:"jobLogId" gorm:"column:id;primaryKey"` //表示主键
	JobName       string    `json:"jobName" gorm:"column:name"`
	JobGroup      string    `json:"jobGroup" gorm:"-"`     // dump 无此列
	InvokeTarget  string    `json:"invokeTarget" gorm:"-"` // dump 无此列
	JobMessage    string    `json:"jobMessage" gorm:"column:msg"`
	ExceptionInfo string    `json:"exceptionInfo" gorm:"-"` // dump 无此列
	StartTime     string    `json:"startTime" gorm:"column:sttim"`
	StopTime      string    `json:"stopTime" gorm:"column:entim"`
	Status        string    `json:"status" gorm:"column:ret"`
	CreateTime    time.Time `json:"createTime" gorm:"-"` // dump 无此列
}

// TableName 指定数据库表名称
func (SysJobLog) TableName() string {
	return "mon_job_log"
}

func SelectJobList(params tools.SearchTableDataParam, isPage bool) ([]SysJob, int64) {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysJob := params.Other.(SysJob)

	var jobName = sysJob.JobName
	var jobGroup = sysJob.JobGroup
	var status = sysJob.Status
	var invokeTarget = sysJob.InvokeTarget

	var total int64
	db := mysql.MysqlDb().Model(SysJob{})

	if jobName != "" {
		db.Where("name like ?", "%"+jobName+"%")
	}
	if jobGroup != "" {
		// dump 无 job_group 列，忽略该条件
		_ = jobGroup
	}
	if status != "" {
		db.Where("status = ?", status)
	}
	if invokeTarget != "" {
		db.Where("code like concat('%', ?, '%')", invokeTarget)
	}

	if err := db.Count(&total).Error; err != nil {
		return nil, 0
	}

	var list []SysJob
	if isPage {
		offset := (pageNum - 1) * pageSize
		db.Order("id DESC").Offset(offset).Limit(pageSize).Find(&list)
	} else {
		db.Order("id DESC").Find(&list)
	}
	return list, total
}

func FindJobById(jobId string) SysJob {
	var job SysJob
	err := mysql.MysqlDb().Where("id = ?", jobId).First(&job).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return job
}

func SaveJob(jobParam SysJobParam, userId interface{}) R.Result {
	var job SysJob
	err := copier.Copy(&job, jobParam)
	job.CreateTime = time.Now()
	user := system.FindUserById(userId)
	job.CreateBy = user.UserName
	err = mysql.MysqlDb().Model(&SysJob{}).Create(&job).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess("操作成功")
}

func UploadJob(jobParam SysJob, userId interface{}) R.Result {
	var job SysJob
	err := copier.Copy(&job, jobParam)
	user := system.FindUserById(userId)
	job.UpdateBy = user.UserName
	job.UpdateTime = time.Now()
	err = mysql.MysqlDb().Model(&SysJob{}).Create(&jobParam).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess("操作成功")
}

func SelectJobLogList(params tools.SearchTableDataParam) ([]SysJobLog, int64) {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysJobLog := params.Other.(SysJobLog)
	var jobName = sysJobLog.JobName
	var jobGroup = sysJobLog.JobGroup
	var status = sysJobLog.Status

	var total int64
	db := mysql.MysqlDb().Model(SysJobLog{})

	if jobName != "" {
		db.Where("name like ?", "%"+jobName+"%")
	}
	if jobGroup != "" {
		// dump 无 job_group 列，忽略该条件
		_ = jobGroup
	}

	if status != "" {
		db.Where("status = ?", status)
	}
	// mon_job_log 无创建时间列，忽略 beginTime/endTime 条件

	if err := db.Count(&total).Error; err != nil {
		return nil, 0
	}
	offset := (pageNum - 1) * pageSize
	var list []SysJobLog
	db.Order("id DESC").Offset(offset).Limit(pageSize).Find(&list)
	return list, total
}

func FindJobLogById(id string) R.Result {
	var jobLog SysJobLog
	err := mysql.MysqlDb().Where("id = ?", id).First(&jobLog).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return R.ReturnSuccess(jobLog)
}

func (param *SysJobLog) JobLogAdd() R.Result {
	param.CreateTime = time.Now()
	if err := mysql.MysqlDb().Model(&SysJobLog{}).Create(&param).Error; err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}

func DetectJob(jobIds string) {
	if err := mysql.MysqlDb().Where("id in ( ? )", jobIds).Delete(&SysJob{}).Error; err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
}

func ChangeStatus(jobId string, status string) {
	err := mysql.MysqlDb().Model(&SysJob{}).Where("id", jobId).Updates("status=" + status).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
}

func DetectJobLog(ids string) {
	err := mysql.MysqlDb().Where("id in ( ? )", utils2.Split(ids)).Delete(&SysJobLog{}).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
}

func ClearJobLog() R.Result {
	if err := mysql.MysqlDb().Exec("truncate table mon_job_log").Error; err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}
