package system

import (
	"time"

	"github.com/x-thooh/thooh-admin/app/admin/model/tools"
	utils2 "github.com/x-thooh/thooh-admin/app/core/utils"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

type SysConfig struct {
	ConfigId    int       `json:"configId" gorm:"column:id;primaryKey"` //表示主键
	ConfigName  string    `json:"configName" gorm:"column:name"`
	ConfigKey   string    `json:"configKey" gorm:"column:kenam"`
	ConfigValue string    `json:"configValue" gorm:"column:keval"`
	ConfigType  string    `json:"configType" gorm:"-"` // dump 无此列
	CreateBy    string    `json:"createBy" gorm:"-"`   // dump 无此列
	UpdateBy    string    `json:"updateBy" gorm:"-"`   // dump 无此列
	CreateTime  time.Time `json:"createTime" gorm:"column:crtim;type:datetime;autoCreateTime"`
	UpdateTime  time.Time `json:"updateTime" gorm:"column:uptim;type:datetime;autoUpdateTime"`
	Remark      string    `json:"remark" gorm:"column:notes"`
}

// TableName 指定数据库表名称
func (SysConfig) TableName() string {
	return "sys_config"
}

func SelectConfigList(params tools.SearchTableDataParam, isPage bool) tools.TableDataInfo {
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysRoles := params.Other.(SysConfig)
	offset := (pageNum - 1) * pageSize
	var total int64
	var rows []SysConfig

	var db = mysql.MysqlDb().Model(&rows)

	var configId = sysRoles.ConfigId
	if configId != 0 {
		db.Where("id = ?", configId)
	}

	var configKey = sysRoles.ConfigKey
	if configKey != "" {
		db.Where("kenam = ?", configKey)
	}

	var configName = sysRoles.ConfigName
	if configName != "" {
		db.Where("name like concat('%', ?, '%')", configName)
	}

	var beginTime = params.Params.BeginTime
	var endTime = params.Params.EndTime

	if beginTime != "" {
		startTime1, endTime1 := utils2.GetBeginAndEndTime(beginTime, endTime)
		db.Where("crtim >= ?", startTime1)
		db.Where("crtim <= ?", endTime1)
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

func SelectConfig(config SysConfig) SysConfig {
	var result SysConfig
	var dbg = mysql.MysqlDb().Model(&result)
	var configId = config.ConfigId
	if configId != 0 {
		dbg.Where("id = ?", configId)
	}
	var configKey = config.ConfigKey
	if configKey != "" {
		dbg.Where("kenam = ?", configKey)
	}
	err := dbg.First(&result).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return result
}

func GetConfigInfo(configId interface{}) SysConfig {
	/*方式一*/
	//var sql = "select config_id, config_name, config_key, config_value, config_type, create_by, create_time, update_by, update_time, remark from sys_config where id = ?"
	var config SysConfig
	//mysql.MysqlDb().Raw(sql, configId).Find(&config)
	/*方式二*/
	err := mysql.MysqlDb().Where("id = ?", configId).First(&config).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return config
}

func SaveConfig(config SysConfig) R.Result {
	/*参数键名是否存在*/
	var keyCount = checkConfigKeyUnique(config.ConfigKey)
	if keyCount > 0 {
		return R.ReturnFailMsg("新增参数'" + config.ConfigName + "'失败，参数键名已存在")
	}
	err := mysql.MysqlDb().Model(&SysConfig{}).Create(&config).Error
	if err == nil {
		return R.ReturnSuccess("操作成功")
	} else {
		return R.ReturnFailMsg(err.Error())
	}
}

func checkConfigKeyUnique(configKey string) int64 {
	var keyCount int64
	err := mysql.MysqlDb().Model(&SysConfig{}).Where("kenam = ?", configKey).Count(&keyCount).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return keyCount
}

func SelectConfigByKey(configKey string) string {
	var config SysConfig
	err := mysql.MysqlDb().Where("kenam = ?", configKey).First(&config).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return config.ConfigValue
}

func EditConfig(config SysConfig) R.Result {
	err := mysql.MysqlDb().Updates(&config).Error
	if err == nil {
		return R.ReturnSuccess("操作成功")
	} else {
		return R.ReturnFailMsg(err.Error())
	}
}

func DelConfig(configIds string) R.Result {
	var ids = utils2.Split(configIds)
	for i := 0; i < len(ids); i++ {
		id := ids[i]
		DelConfigById(id)
	}
	return R.ReturnSuccess("操作成功")
}

func DelConfigById(configId int) {
	err := mysql.MysqlDb().Where("id = ?", configId).Delete(&SysConfig{}).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
}
