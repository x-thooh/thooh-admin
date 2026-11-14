package pub

import (
	"fmt"
	"net/http"
	"strconv"

	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/common/r"
	"github.com/x-thooh/thooh-admin/modules/sys/menu"
	"github.com/x-thooh/thooh-admin/pkg/mysql"

	"github.com/gin-gonic/gin"
)

func GetActor(c *gin.Context) {
	//typ := c.Param("type")
	//pid := c.Param("pid")
	var list []IdNameAvatarVo
	uid, ok := currentUserId(c)
	if !ok {
		return
	}
	err := mysql.MysqlDb().Raw(userActorSQL, uid).Scan(&list).Error
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	c.JSON(http.StatusOK, r.Ok(list))
}

func GetRece(c *gin.Context) {
	//var list []IdNameOrgVo
	c.JSON(http.StatusOK, r.Ok([0]IdNameOrgVo{}))
}

func GetGroupTree(c *gin.Context) {
	//var list []IdNameOrgVo
	c.JSON(http.StatusOK, r.Ok([0]r.Stree{}))
}

func PostRece(c *gin.Context) {
	c.JSON(http.StatusOK, r.Ok(0))
}

// currentUserId 取 Gate 中间件放进 gin.Context 的 userId，缺失即未登录。
func currentUserId(c *gin.Context) (string, bool) {
	id, ok := c.Get("userId")
	if !ok {
		c.JSON(http.StatusOK, R.ReturnFailMsg("未登录"))
		return "", false
	}
	return fmt.Sprint(id), true
}

// 用户→角色(sys_role_actor.aid=用户ID)→菜单(sys_role_menu)
const userMenuSQL = "select distinct m.shtag,m.type,m.name,m.path,m.icon,m.comp,m.ornum,m.id,m.pid,m.outag,m.catag from sys_menu m " +
	"join sys_role_menu rm on rm.mid=m.id join sys_role_actor ra on ra.rid=rm.rid " +
	"where m.avtag=1 and ra.aid=? order by m.pid,m.ornum"

// 与当前用户同角色的参与者
const userActorSQL = "select distinct a.id,a.name from sys_actor a join sys_role_actor ra on ra.aid=a.id " +
	"where ra.rid in (select rid from sys_role_actor where aid=?)"

func GetUser(c *gin.Context) {
	uid, ok := currentUserId(c)
	if !ok {
		return
	}
	db := mysql.MysqlDb()
	var user User
	err := db.Raw("select u.id useid,u.name nicna,u.orgid,u.email,u.monum,u.gender,u.avatar from sys_user u where u.id=?", uid).Scan(&user).Error
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	if user.Useid == "" {
		c.JSON(http.StatusOK, R.ReturnFailMsg("用户不存在"))
		return
	}
	user.Usena = user.Nicna
	var rids []int64
	if err = db.Raw("select rid from sys_role_actor where aid=?", uid).Scan(&rids).Error; err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	var vo UserInfoVo
	vo.User = user
	for _, rid := range rids {
		vo.Roles = append(vo.Roles, strconv.FormatInt(rid, 10))
		if rid == 1 {
			vo.Roles = append(vo.Roles, "superadmin")
			vo.Perms = append(vo.Perms, "*:*:*")
		}
	}
	c.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
		"data": vo,
	})
}

func GetMenus(c *gin.Context) {
	var menuList []menu.SysMenu
	uid, ok := currentUserId(c)
	if !ok {
		return
	}
	err := mysql.MysqlDb().Raw(userMenuSQL, uid).Scan(&menuList).Error
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	menuList = GetChildPerms(menuList, 0)
	menuVoList := buildMenus(menuList)

	c.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
		"data": menuVoList,
	})
}
