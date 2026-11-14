package error

import (
	"encoding/json"
	"log"
	"net/http"
	"runtime/debug"

	"github.com/x-thooh/thooh-admin/app/admin/service/monitor"
	"github.com/x-thooh/thooh-admin/app/core/utils/R"

	"github.com/gin-gonic/gin"
)

// Recover 只兜意料之外的崩溃：业务失败由 handler 直接 c.JSON 返回，不再走 panic。
// 崩溃时打一条错误加栈，对客户端只回通用提示，不泄露内部细节。
// 仍遗留 panic(R.Result) 的旧代码（admin/demo、tools/gen）按业务失败处理，只打一行不打栈。
func Recover(context *gin.Context) {
	defer func() {
		if r := recover(); r != nil {
			res, legacy := r.(R.Result)
			if legacy {
				log.Printf("业务失败(panic): %s", res.Msg)
			} else {
				log.Printf("panic: %v\n%s", r, debug.Stack())
				res = R.ReturnFailMsg("系统异常，请联系管理员")
			}
			data, _ := json.Marshal(res)
			monitor.SysOperLog.AddSysOperLog(context, string(data))
			context.JSON(http.StatusOK, res)
			//终止后续接口调用，不加的话recover到异常后，还会继续执行接口里后续代码
			context.Abort()
		}
	}()
	context.Next()
}
