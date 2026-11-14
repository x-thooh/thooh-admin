package lolog

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"

	"github.com/x-thooh/thooh-admin/common/json/boolx"
	"github.com/x-thooh/thooh-admin/common/json/timex"
	"github.com/x-thooh/thooh-admin/common/utils"
	"github.com/x-thooh/thooh-admin/pkg/mysql"

	"github.com/gin-gonic/gin"
	useragent "github.com/wenlng/go-user-agent"
	"golang.org/x/text/encoding/simplifiedchinese"
	"golang.org/x/text/transform"
)

func Insert(c *gin.Context, username string, message string, loginSucess bool) {
	userAgent := c.Request.Header.Get("User-Agent")
	Os := useragent.GetOsName(userAgent)
	browser := useragent.GetBrowserName(userAgent)
	var entry = MonLoginLog{
		Id:       utils.NextId(),
		Username: username,
		//Tenid:    "0000",
		Himsg:   message,
		Loip:    c.ClientIP(),
		Loloc:   GetRealAddressByIP(c.ClientIP()),
		Browser: browser,
		Os:      Os,
		Sutag:   boolx.Bool(loginSucess),
		Lotim:   timex.Time(time.Now()),
	}

	//Clkey    string     `json:"clkey" gorm:"type:varchar(32)"`    //客户端key
	//Detyp    string     `json:"detyp" gorm:"type:varchar(8)"`     //设备类型

	err := mysql.MysqlDb().Create(&entry).Error
	if err != nil {
		// 登录日志写失败不应影响登录结果，只记一行
		log.Printf("登录日志写入失败: %v", err)
	}
}

type Tunit struct {
	IP   string `json:"ip"`
	Pro  string `json:"pro"`
	City string `json:"city"`
}

func GetRealAddressByIP(ip string) string {
	url := "http://whois.pconline.com.cn/ipJson.jsp?ip=" + ip + "&json=true"

	resp, err := http.Get(url)
	if err != nil {
		return "内网IP"
	}
	defer resp.Body.Close()

	// 读取原始数据
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "内网IP"
	}

	// 将 GBK 转换为 UTF-8
	reader := transform.NewReader(bytes.NewReader(body), simplifiedchinese.GBK.NewDecoder())
	utf8Body, err := ioutil.ReadAll(reader)
	if err != nil {
		return "内网IP"
	}

	// 解析 JSON
	var dws Tunit
	if err := json.Unmarshal(utf8Body, &dws); err != nil {
		return "内网IP"
	}

	// 检查是否为空
	if dws.Pro == "" && dws.City == "" {
		return "内网IP"
	}

	return fmt.Sprintf("%s %s", dws.Pro, dws.City)
}
