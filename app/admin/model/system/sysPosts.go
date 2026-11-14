package system

import (
	"github.com/x-thooh/thooh-admin/app/admin/model/tools"
	"github.com/x-thooh/thooh-admin/app/core/utils"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
	"time"
)

// SysPost model：数据库字段
type SysPost struct {
	PostId     string    `json:"postId" gorm:"column:id;primaryKey"` //表示主键
	PostCode   string    `json:"postCode" gorm:"column:label"`
	PostName   string    `json:"postName" gorm:"column:name"`
	PostSort   int       `json:"postSort" gorm:"column:ornum"`
	Status     string    `json:"status" gorm:"column:avtag"`
	CreateBy   string    `json:"createBy" gorm:"-"`
	CreateTime time.Time `json:"createTime" gorm:"column:crtim;type:datetime;autoCreateTime"`
	UpdateBy   string    `json:"updateBy" gorm:"-"`
	UpdateTime time.Time `json:"updateTime" gorm:"column:uptim;type:datetime;autoCreateTime"`
	Remark     string    `json:"remark" gorm:"column:notes"`
}

// TableName 指定数据库表名称
func (SysPost) TableName() string {
	return "sys_post"
}

func SelectUserPostGroup(userName string) string {
	var posts []SysPost
	var result = ""
	mysql.MysqlDb().Raw("select p.id as post_id, p.name as post_name, p.label as post_code "+
		"from sys_post p "+
		"left join sys_post_actor up on up.pid = p.id "+
		"left join sys_user u on u.id = up.aid "+
		"where u.username = ?", userName).Scan(&posts)
	if posts != nil {
		for i := range posts {
			sysPost := posts[i]
			if i == 0 {
				result = sysPost.PostName
			} else {
				result += "," + sysPost.PostName
			}
		}
	}
	return result
}

// 分页查询
func SelectSysPostList(params tools.SearchTableDataParam, isPage bool) tools.TableDataInfo {

	var pageNum = params.PageNum
	var pageSize = params.PageSize
	sysPost := params.Other.(SysPost)

	offset := (pageNum - 1) * pageSize
	var total int64
	var rows []SysPost

	var db = mysql.MysqlDb().Model(&rows)

	var postCode = sysPost.PostCode
	if postCode != "" {
		db.Where("label like ?", "%"+postCode+"%")
	}
	var status = sysPost.Status
	if status != "" {
		db.Where("avtag = ?", status)
	}
	var postName = sysPost.PostName
	if postName != "" {
		db.Where("name like ?", "%"+postName+"%")
	}

	db.Order("ornum")

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

func SelectPostListByUserId(userId string) []string {
	var result []string
	mysql.MysqlDb().Raw("select p.id "+
		"from sys_post p "+
		"left join sys_post_actor up on up.pid = p.id "+
		"left join sys_user u on u.id = up.aid "+
		"where u.id = ? ", userId).Find(&result)
	return result
}

/*
*添加 岗位和用户关联
 */
func AddPostByUser(user SysUserParm) {
	postIds := user.PostIds
	userId := user.UserId
	AddPostListByUser(postIds, userId)
}

func AddPostListByUser(postIds []string, userId string) {
	var posts []SysUserPost
	for i := 0; i < len(postIds); i++ {
		var post = SysUserPost{
			PostId: postIds[i],
			UserId: userId,
		}
		posts = append(posts, post)
	}
	if len(posts) == 0 {
		return // WHY: 没选岗位时 CreateInBatches(x, 0) 会失败（浏览器新增用户实测）
	}
	err := mysql.MysqlDb().CreateInBatches(posts, len(posts)).Error
	if err != nil {
		panic(R.ReturnFailMsg("添加 部门管理用户失败"))
	}
}

// 删除关联用户
func DeletePostByUser(userIds []string) {
	err := mysql.MysqlDb().Exec("delete from sys_post_actor where aid in (?) ", userIds).Error
	if err != nil {
		panic(R.ReturnFailMsg("删除部门关联用户失败"))
	}
}

func FindPostInfoById(postId string) SysPost {
	var post SysPost
	err := mysql.MysqlDb().Where("id = ?", postId).First(&post).Error
	if err != nil {
		panic(R.ReturnFailMsg(err.Error()))
	}
	return post
}

func SavePost(post SysPost) R.Result {
	err := mysql.MysqlDb().Model(&SysPost{}).Create(&post).Error
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}

func EditPost(sysPost SysPost) R.Result {
	err := mysql.MysqlDb().Updates(&sysPost).Error
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}

func DeletePost(postIds string) R.Result {
	err := mysql.MysqlDb().Where("id in (?)", utils.Split(postIds)).Delete(&SysPost{}).Error
	if err != nil {
		return R.ReturnFailMsg(err.Error())
	}
	return R.ReturnSuccess("操作成功")
}
