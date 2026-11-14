package user

import (
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/common/json/timex"
	"github.com/x-thooh/thooh-admin/common/r"
	"github.com/x-thooh/thooh-admin/common/utils"
	"github.com/x-thooh/thooh-admin/modules/sys/actor"
	"github.com/x-thooh/thooh-admin/pkg/mysql"

	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
)

// Get 用户列表
// @Summary 用户列表
// @Tags user
// @Param pageNum query int false "页码"
// @Param pageSize query int false "每页条数"
// @Success 200 {object} r.R "成功"
// @Router /sys/user [get]
func Get(c *gin.Context) {
	pageNum, _ := strconv.Atoi(c.DefaultQuery("pageNum", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("pageSize", "10"))
	var list []SysUser
	queryDB := mysql.MysqlDb().Model(&SysUser{})
	pagination := &r.PaginationQuery{
		Page:     pageNum,
		PageSize: pageSize,
	}
	paginate, err := r.Paginate(queryDB, &list, pagination)
	if err != nil {
		return
	}
	for i := range paginate.Rows {
		paginate.Rows[i].Password = "" // WHY: 列表出站不吐口令散列（T-31）
	}
	c.JSON(http.StatusOK, r.Ok(paginate))
}

// GetInfo 用户详情
// @Summary 用户详情
// @Tags user
// @Param id path string true "用户ID"
// @Success 200 {object} r.R "成功"
// @Router /sys/user/info/{id} [get]
func GetInfo(c *gin.Context) {
	id := c.Param("id")
	var main SysUser
	mysql.MysqlDb().First(&main, "id = ?", id)
	if main.Id == "" {
		c.JSON(http.StatusOK, R.ReturnFailMsg("未找到记录"))
		return
	}
	main.Password = "" // WHY: 详情出站不吐口令散列（T-31）
	c.JSON(http.StatusOK, r.Ok(main))
}

// Post 新增用户
// @Summary 新增用户
// @Tags user
// @Accept json
// @Produce json
// @Param body body SysUser true "用户"
// @Success 200 {object} r.R "成功"
// @Router /sys/user [post]
func Post(c *gin.Context) {
	var main SysUser
	if err := c.ShouldBindBodyWith(&main, binding.JSON); err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	main.Id = utils.NextIdStr()
	main.Crtim = timex.Time(time.Now())
	main.Uptim = main.Crtim
	err := mysql.MysqlDb().Create(&main).Error
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	var sysActor actor.SysActor
	sysActor.Id = main.Id
	sysActor.Name = main.Name
	sysActor.Type = 2
	err = mysql.MysqlDb().Create(&sysActor).Error
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	c.JSON(http.StatusOK, r.Ok(main.Id))

}

// Put 更新用户
// @Summary 更新用户
// @Tags user
// @Accept json
// @Produce json
// @Param body body SysUser true "用户"
// @Success 200 {object} r.R "成功"
// @Router /sys/user [put]
func Put(c *gin.Context) {
	var main SysUser
	if err := c.ShouldBindBodyWith(&main, binding.JSON); err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	main.Uptim = timex.Time(time.Now())
	err := mysql.MysqlDb().Select("*").Omit("crtim,cruid").Updates(&main).Error
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	mysql.MysqlDb().Model(&actor.SysActor{}).Where("id = ?", main.Id).Update("name", main.Name)
	c.JSON(http.StatusOK, r.Ok(main.Id))

}

// Delete 删除用户
// @Summary 删除用户
// @Tags user
// @Param ids path string true "用户ID，逗号分隔"
// @Success 200 {object} r.R "成功"
// @Router /sys/user/{ids} [delete]
func Delete(c *gin.Context) {
	var ids = c.Param("ids")
	arr := strings.Split(ids, ",")
	for i := 0; i < len(arr); i++ {
		err := mysql.MysqlDb().Where("id = ?", arr[i]).Delete(&SysUser{}).Error
		if err != nil {
			c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
			return
		}
	}
	c.JSON(http.StatusOK, r.Ok(len(arr)))
}
