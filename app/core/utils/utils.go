package utils

import (
	"fmt"
	"github.com/goccy/go-json"
	"io/ioutil"
	"net"
	"net/http"
	"strconv"
	"strings"
	"time"
)

func GetInterfaceToInt(t1 interface{}) int {
	var t2 int
	switch t1.(type) {
	case uint:
		t2 = int(t1.(uint))
		break
	case int8:
		t2 = int(t1.(int8))
		break
	case uint8:
		t2 = int(t1.(uint8))
		break
	case int16:
		t2 = int(t1.(int16))
		break
	case uint16:
		t2 = int(t1.(uint16))
		break
	case int32:
		t2 = int(t1.(int32))
		break
	case uint32:
		t2 = int(t1.(uint32))
		break
	case int64:
		t2 = int(t1.(int64))
		break
	case uint64:
		t2 = int(t1.(uint64))
		break
	case float32:
		t2 = int(t1.(float32))
		break
	case float64:
		t2 = int(t1.(float64))
		break
	case string:
		t2, _ = strconv.Atoi(t1.(string))
		break
	default:
		t2 = t1.(int)
		break
	}
	return t2
}

// GetRemoteClientIp 获取远程客户端IP
func GetRemoteClientIp(r *http.Request) string {
	remoteIp := r.RemoteAddr

	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		remoteIp = ip
	} else if ip = r.Header.Get("X-Forwarded-For"); ip != "" {
		remoteIp = ip
	} else {
		remoteIp, _, _ = net.SplitHostPort(remoteIp)
	}

	//本地ip
	if remoteIp == "::1" {
		remoteIp = "127.0.0.1"
	}

	return remoteIp
}

type Tunit struct {
	Pro  string `json:"pro"`
	City string `json:"city"`
}

func GetRealAddressByIP(ip string) string {
	url := "http://whois.pconline.com.cn/ipJson.jsp?ip=" + ip + "&json=true"
	resp, err := http.Get(url)
	var result = "内网ip"
	if err != nil {
		result = "内网ip"
	} else {
		defer resp.Body.Close()
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			result = "内网ip"
		} else {
			dws := new(Tunit)
			json.Unmarshal(body, &dws)
			result = dws.Pro + " " + dws.City
		}
	}
	return result
}

// 数组转 string,
func Join(sep []int, sp string) string {
	sarr := make([]string, len(sep))
	for i, v := range sep {
		sarr[i] = fmt.Sprint(v)
	}
	return strings.Join(sarr, fmt.Sprint(sp))
}

// GetInterfaceToStr 把 ctx 里的身份值转成 string。
// WHY: dump 的 sys_user.id / sys_org.id 是 varchar(36)（u1/o1000），鉴权中间件往
// ctx 放的就是这个字符串；用 GetInterfaceToInt 会把它变成 0，进而误判「不是超管」。
func GetInterfaceToStr(v interface{}) string {
	if v == nil {
		return ""
	}
	switch t := v.(type) {
	case string:
		return t
	case []byte:
		return string(t)
	default:
		return fmt.Sprint(t)
	}
}

// string转数组
/* 1,1,2,3,4,5*/
func Split(data string) []int {
	var sa = strings.Split(data, ",")
	var sarr []int
	for i := 0; i < len(sa); i++ {
		var v = sa[i]
		var v1, _ = strconv.Atoi(v)
		sarr = append(sarr, v1)
	}
	return sarr
}

// string转数组
/* 1,1,2,3,4,5*/
func SplitStr(data string) []string {
	var sa = strings.Split(data, ",")
	var sarr []string
	for i := 0; i < len(sa); i++ {
		var v = sa[i]
		sarr = append(sarr, v)
	}
	return sarr
}

// 字节的单位转换 保留两位小数
func FormatFileSize(fileSize uint64) (size string) {
	if fileSize < 1024 {
		//return strconv.FormatInt(fileSize, 10) + "B"
		return fmt.Sprintf("%.2fB", float64(fileSize)/float64(1))
	} else if fileSize < (1024 * 1024) {
		return fmt.Sprintf("%.2fKB", float64(fileSize)/float64(1024))
	} else if fileSize < (1024 * 1024 * 1024) {
		return fmt.Sprintf("%.2fMB", float64(fileSize)/float64(1024*1024))
	} else if fileSize < (1024 * 1024 * 1024 * 1024) {
		return fmt.Sprintf("%.2fGB", float64(fileSize)/float64(1024*1024*1024))
	} else if fileSize < (1024 * 1024 * 1024 * 1024 * 1024) {
		return fmt.Sprintf("%.2fTB", float64(fileSize)/float64(1024*1024*1024*1024))
	} else { //if fileSize < (1024 * 1024 * 1024 * 1024 * 1024 * 1024)
		return fmt.Sprintf("%.2fPB", float64(fileSize)/float64(1024*1024*1024*1024*1024))
	}
}

// FirstUpper 字符串首字母大写
func FirstUpper(s string) string {
	if s == "" {
		return ""
	}
	return strings.ToUpper(s[:1]) + s[1:]
}

func GetDbType(dt string) string {
	switch dt {
	case "varchar":
		return "string"
	case "datetime":
		return "time.Time"
	case "timestamp":
		return "time.Time"
	case "double":
		return "float64"
	case "float":
		return "float64"
	case "decimal":
		return "float64"
	case "int":
		return "int64"
	case "tinyint":
		return "int64"
	case "smallint":
		return "int64"
	case "mediumint":
		return "int64"
	case "integer":
		return "int64"
	case "bigint":
		return "int64"
	default:
		return "string"
	}
}

func RemoveEmpty(arr []string) (result []string) {
	for _, value := range arr {
		if len(value) > 0 { // 判断字符串长度大于零则添加到结果数组中
			result = append(result, value)
		}
	}
	return
}

// NextIntId 给 dump 里「bigint 主键但没有 auto_increment」的表造主键。
// WHY: mon_oper_log / mon_login_log / mon_job / sys_notice / tool_dict* / sys_config /
// sys_menu / sys_role 的 id 都不自增，INSERT 不显式给值就是 1364 Field 'id' doesn't
// have a default value（浏览器与接口实测，审计驳回的正是这一类）。
func NextIntId() int64 {
	return time.Now().UnixNano() / 1000
}

// NextStrId 给 varchar(36) 主键的表（sys_user / sys_org / sys_post）造主键。
func NextStrId(prefix string) string {
	return prefix + strconv.FormatInt(time.Now().UnixNano(), 36)
}
