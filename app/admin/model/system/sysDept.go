package system

import (
	"github.com/x-thooh/thooh-admin/common/json/bitx"
	"time"

	"github.com/x-thooh/thooh-admin/app/admin/model/tools"
	"github.com/x-thooh/thooh-admin/app/core/utils"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

// SysDept model：数据库字段
type SysDept struct {
	DeptId     string    `json:"deptId" gorm:"column:id;primaryKey"` //表示主键
	ParentId   string    `json:"parentId" gorm:"column:pid"`
	Ancestors  string    `json:"ancestors" gorm:"-"`
	DeptName   string    `json:"deptName" gorm:"column:name"`
	OrderNum   int       `json:"orderNum" gorm:"column:ornum"`
	Leader     string    `json:"leader" gorm:"-"`
	Phone      string    `json:"phone" gorm:"-"`
	Email      string    `json:"email" gorm:"-"`
	Status     bitx.Str  `json:"status" gorm:"column:avtag"`
	DelFlag    string    `json:"delFlag" gorm:"-"`
	CreateBy   string    `json:"createBy" gorm:"-"`
	CreateTime time.Time `json:"createTime" gorm:"column:crtim;type:datetime;autoCreateTime"`
	UpdateBy   string    `json:"updateBy" gorm:"-"`
	UpdateTime time.Time `json:"updateTime" gorm:"column:uptim;type:datetime;autoCreateTime"`
}

type SysDeptResult struct {
	DeptId     string          `json:"deptId" gorm:"column:id;primaryKey"` //表示主键
	ParentId   string          `json:"parentId" gorm:"column:pid"`
	Ancestors  string          `json:"ancestors" gorm:"-"`
	DeptName   string          `json:"deptName" gorm:"column:name"`
	OrderNum   int             `json:"orderNum" gorm:"column:ornum"`
	Leader     string          `json:"leader" gorm:"-"`
	Phone      string          `json:"phone" gorm:"-"`
	Email      string          `json:"email" gorm:"-"`
	Status     bitx.Str        `json:"status" gorm:"column:avtag"`
	ParentName string          `json:"parentName" gorm:"-"`
	Children   []SysDeptResult `json:"children"`
	CreateBy   string          `json:"createBy" gorm:"-"`
	CreateTime time.Time       `json:"createTime" gorm:"column:crtim;type:datetime"`
	UpdateBy   string          `json:"updateBy" gorm:"-"`
	UpdateTime time.Time       `json:"updateTime" gorm:"column:uptim;type:datetime"`
}

// TableName 指定数据库表名称
func (SysDept) TableName() string {
	return "sys_org"
}

type SysDeptDto struct {
	Id string `json:"id"`
	/** 节点名称 */
	Label string `json:"label"`
	/** 子节点 */
	Children []SysDeptDto `json:"children"`
}

// 分页查询
func GetDeptList(params tools.SearchTableDataParam, isPaging bool) ([]SysDeptResult, int64) {
	var total int64
	var pageNum = params.PageNum
	var pageSize = params.PageSize
	offset := (pageNum - 1) * pageSize
	dept := params.Other.(SysDept)

	var list []SysDeptResult
	var db = mysql.MysqlDb().Model(&[]SysDept{})

	var deptId = dept.DeptId
	if deptId != "" {
		db.Where("id = ?", deptId)
	}

	var parentId = dept.ParentId
	if parentId != "" {
		db.Where("pid = ?", parentId)
	}

	var deptName = dept.DeptName
	if deptName != "" {
		db.Where("name like concat('%', ?, '%')", deptName)
	}

	var status = dept.Status
	if status != "" {
		db.Where("avtag = ?", status)
	}
	db.Order("pid, ornum")

	if err := db.Count(&total).Error; err != nil {
		return nil, 0
	}
	if isPaging {
		if err := db.Offset(offset).Limit(pageSize).Find(&list).Error; err != nil {
			return nil, 0
		}
	} else {
		if err := db.Find(&list).Error; err != nil {
			return nil, 0
		}
	}

	return list, total
}

func GetDeptInfo(deptId string) SysDept {
	var dept SysDept
	err := mysql.MysqlDb().Where("id = ?", deptId).First(&dept).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return dept
}

func SaveDept(sysDept SysDept) R.Result {
	sysDept.DelFlag = "0"
	if sysDept.DeptId == "" {
		sysDept.DeptId = utils.NextStrId("o")
	}
	err := mysql.MysqlDb().Model(&sysDept).Create(&sysDept).Error
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}

func UpDataDept(sysDept SysDept) R.Result {
	err := mysql.MysqlDb().Updates(&sysDept).Error
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}

/*单个删除*/
func DeleteDept(deptId string) R.Result {
	//if (deptService.hasChildByDeptId(deptId))
	//        {
	//            return AjaxResult.error("存在下级部门,不允许删除");
	//        }
	//        if (deptService.checkDeptExistUser(deptId))
	//        {
	//            return AjaxResult.error("部门存在用户,不允许删除");
	//        }
	//是否有数据权限
	err := mysql.MysqlDb().Where("id = ?", deptId).Delete(&SysDept{}).Error
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}

type TreeSelect struct {
	Id       string       `json:"id"`
	Label    string       `json:"label"`
	Children []TreeSelect `json:"children"`
}

func SelectDeptTreeList() []TreeSelect {
	var deptResults []TreeSelect
	var depts []SysDept
	err := mysql.MysqlDb().Order("pid, ornum").Find(&depts).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}

	for i := 0; i < len(depts); i++ {
		dept := depts[i]
		deptId := dept.DeptId
		name := dept.DeptName
		pId := dept.ParentId
		if pId == "" {
			tChild := getChildList(depts, deptId)
			treeSelect := TreeSelect{
				Id:       deptId,
				Label:    name,
				Children: tChild,
			}
			deptResults = append(deptResults, treeSelect)
		}
	}

	return deptResults
}

func getChildList(depts []SysDept, deptId string) []TreeSelect {
	var tlist []TreeSelect
	for i := 0; i < len(depts); i++ {
		dept1 := depts[i]
		id := dept1.DeptId
		pId := dept1.ParentId
		name := dept1.DeptName

		if pId == deptId {
			tChild := getChildList(depts, id)
			tree := TreeSelect{
				Id:       id,
				Label:    name,
				Children: tChild,
			}
			tlist = append(tlist, tree)
		}

	}
	return tlist
}
