package system

import (
	"github.com/gin-gonic/gin"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"
	"net/http"
)

// 后台获取 首页数据

func IndexData() {
	//
}

// IndexHandler 测试代码
func IndexHandler(context *gin.Context) {
	context.JSON(http.StatusOK, R.ReturnSuccess("Hello ruoyi go"))
}
