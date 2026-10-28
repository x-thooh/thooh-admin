package monitor

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/x-thooh/thooh-admin/app/admin/model/monitor"
)

func ServerData(context *gin.Context) {
	var server = monitor.GetServerInfo(context)
	context.JSON(http.StatusOK, gin.H{
		"msg":  "操作成功",
		"code": http.StatusOK,
		"data": server,
	})
}
