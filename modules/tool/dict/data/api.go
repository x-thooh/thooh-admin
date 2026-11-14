package dictd

import (
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"github.com/x-thooh/thooh-admin/common/json/timex"
	"github.com/x-thooh/thooh-admin/common/r"
	"github.com/x-thooh/thooh-admin/common/utils"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
)

func Get(c *gin.Context) {
	pageNum, _ := strconv.Atoi(c.DefaultQuery("pageNum", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("pageSize", "10"))
	dicidStr := c.DefaultQuery("dicid", "0") // 默认值为 "0"
	dicid, err := strconv.ParseInt(dicidStr, 10, 64)
	if err != nil {
		c.JSON(400, gin.H{"error": "参数id格式错误"})
		return
	}

	var list []ToolDictData
	queryDB := mysql.MysqlDb().Model(&ToolDictData{}).Where("dicid = ?", dicid)
	pagination := &r.PaginationQuery{
		Page:     pageNum,
		PageSize: pageSize,
	}
	paginate, err := r.Paginate(queryDB, &list, pagination)
	if err != nil {
		return
	}
	c.JSON(http.StatusOK, r.Ok(paginate))
}

func GetInfo(c *gin.Context) {
	id := c.Param("id")
	var main ToolDictData
	mysql.MysqlDb().First(&main, "id = ?", id)
	if main.Id == 0 {
		c.JSON(http.StatusOK, R.ReturnFailMsg("未找到记录"))
		return
	}
	c.JSON(http.StatusOK, r.Ok(main))
}

func Post(c *gin.Context) {
	var main ToolDictData
	if err := c.ShouldBindBodyWith(&main, binding.JSON); err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	main.Id = utils.NextId()
	main.Crtim = timex.Time(time.Now())
	main.Uptim = main.Crtim
	err := mysql.MysqlDb().Create(&main).Error
	if err != nil {
		c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
		return
	}
	c.JSON(http.StatusOK, r.Ok(main.Id))

}

func Put(c *gin.Context) {
	var main ToolDictData
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
	c.JSON(http.StatusOK, r.Ok(main.Id))
}

func Delete(c *gin.Context) {
	var ids = c.Param("ids")
	arr := strings.Split(ids, ",")
	for i := 0; i < len(arr); i++ {
		err := mysql.MysqlDb().Where("id = ?", arr[i]).Delete(&ToolDictData{}).Error
		if err != nil {
			c.JSON(http.StatusOK, R.ReturnFailMsg(err.Error()))
			return
		}
	}
	c.JSON(http.StatusOK, r.Ok(len(arr)))
}
