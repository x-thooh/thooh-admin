// migrate 显式执行表结构迁移。服务启动不再改表，升级前手动跑 make migrate。
package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/x-thooh/thooh-admin/common/config"
	"github.com/x-thooh/thooh-admin/modules/sys/group"
	"github.com/x-thooh/thooh-admin/modules/sys/groupc"
	"github.com/x-thooh/thooh-admin/pkg/mysql"
)

var configFile = flag.String("f", "./config.yaml", "配置文件路径")

func main() {
	flag.Parse()
	config.InitAppConfig(*configFile)
	err := mysql.MysqlDb().AutoMigrate(&group.SysGroup{}, &groupc.SysGroupCate{}, &group.SysGroupActor{})
	if err != nil {
		fmt.Fprintf(os.Stderr, "迁移失败：%v\n", err)
		os.Exit(1)
	}
	fmt.Println("迁移完成：sys_group / sys_group_cate / sys_group_actor")
}
