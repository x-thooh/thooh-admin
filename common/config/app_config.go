package config

import (
	"io/ioutil"
	"log"
	"os"
	"path"
	"regexp"
	"strings"

	"gopkg.in/yaml.v2"
)

// envRef 认 ${NAME} 与 ${NAME:-默认} 两种写法，不认裸 $NAME：配置文件里合法的美元符号
// （密码、路径）会被顺手吃掉，而那种错一句报错都没有。
var envRef = regexp.MustCompile(`\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}`)

var Server *server
var Database *database
var Redis *redis
var Jwt *jwt
var XxlJob *xxlJob
var LogConfig *logConfig
var UserPassword *userPassword

type conf struct {
	Svc          server       `yaml:"server"`
	DB           database     `yaml:"database"`
	RedisConfig  redis        `yaml:"redis"`
	Jwt          jwt          `yaml:"jwt"`
	XxlJob       xxlJob       `yaml:"xxl-job"`
	LogConfig    logConfig    `yaml:"log"`
	UserPassword userPassword `yaml:"user-password"`
}

type server struct {
	Port           int    `yaml:"port"`
	RunMode        string `yaml:"runMode"`
	LogLevel       string `yaml:"logLevel"`
	EnabledSwagger bool   `yaml:"enabledSwagger"`
}
type database struct {
	Primary         datasource `yaml:"primary"`
	Secondary       datasource `yaml:"secondary"`
	MaxIdleConn     int        `yaml:"max_idle_conn"`
	MaxOpenConn     int        `yaml:"max_open_conn"`
	ConnMaxLifetime int        `yaml:"conn_max_lifetime"`
}
type datasource struct {
	Enabled  bool   `yaml:"enabled"`
	Type     string `yaml:"type"`
	Host     string `yaml:"host"`
	Port     string `yaml:"port"`
	UserName string `yaml:"username"`
	Password string `yaml:"password"`
	DbName   string `yaml:"dbname"`
}
type redis struct {
	Host     string `yaml:"host"`
	Port     string `yaml:"port"`
	Password string `yaml:"password"`
	DB       int    `yaml:"db"`
}

type jwt struct {
	Secret string `yaml:"secret"`
	JwtTtl int    `yaml:"jwt_ttl"`
}

type xxlJob struct {
	Enabled          bool   `yaml:"enabled"`
	Env              string `yaml:"env"`
	AdminAddress     string `yaml:"admin_address"`
	AccessToken      string `yaml:"access_token"`
	AppName          string `yaml:"app_name"`
	Address          string `yaml:"address"`
	Ip               string `yaml:"ip"`
	JobUName         string `yaml:"job_uname"`
	JobUPass         string `yaml:"job_upass"`
	Port             int    `yaml:"port"`
	LogPath          string `yaml:"log_path"`
	LogRetentionDays int    `yaml:"log_retention_days"`
	HttpTimeout      int    `yaml:"http_timeout"`
}

type logConfig struct {
	Enabled  bool     `yaml:"enabled"`
	LogMode  string   `yaml:"logMode"`
	FilePath string   `yaml:"filePath"`
	Filtered []string `yaml:"filtered"`
}
type userPassword struct {
	MaxRetryCount int `yaml:"maxRetryCount"`
	LockTime      int `yaml:"lockTime"`
}

// expandEnv 把配置文本里的 ${NAME} 换成环境变量。没给值又没默认的名字一律收集起来，
// 由调用方一次报全——部署的人跑 N 次才知道还缺第 N+1 个变量，是最难查的一类现场。
// `${NAME:-}` 是「明写允许空」（从库没开时的密码就是这种），和「没给默认」不是一回事，
// 所以判有没有默认要看 `:-` 在不在，不能看捕获到的字符串空不空。
// 逐行处理并跳过注释：注释里写一句「${NAME} 必填」来解释语法，是文档而不是引用，
// 拿它当引用会让一份说明写得越清楚的配置文件越起不来（实测踩过：missing 里冒出 VAR、NAME）。
func expandEnv(raw string) (string, []string) {
	var missing []string
	seen := map[string]bool{}
	refs := func(text string) string {
		return envRef.ReplaceAllStringFunc(text, func(ref string) string {
			groups := envRef.FindStringSubmatch(ref)
			name := groups[1]
			if v, ok := os.LookupEnv(name); ok && v != "" {
				return v
			}
			if strings.Contains(ref, ":-") {
				return groups[2]
			}
			if !seen[name] {
				seen[name] = true
				missing = append(missing, name)
			}
			return ref
		})
	}
	lines := strings.Split(raw, "\n")
	for i, line := range lines {
		body, comment := splitYAMLComment(line)
		lines[i] = refs(body) + comment
	}
	return strings.Join(lines, "\n"), missing
}

// splitYAMLComment 按 YAML 的规矩切注释：# 只有出现在行首或紧跟空白才算注释起点，
// 否则它是值的一部分（URL 的 fragment 就是这种）。
func splitYAMLComment(line string) (string, string) {
	for i := 0; i < len(line); i++ {
		if line[i] != '#' {
			continue
		}
		if i == 0 || line[i-1] == ' ' || line[i-1] == '\t' {
			return line[:i], line[i:]
		}
	}
	return line, ""
}

func InitAppConfig(dataFile string) {
	// 解决相对路经下获取不了配置文件问题
	//_, filename, _, _ := runtime.Caller(0)
	filePath := path.Join("", dataFile)
	// 这里的失败一律走 log.Fatalf 而不是 panic(结构体)：Go 运行时打印不可输出的复合值时
	// 只给 `(R.Result) 0x地址`，实测现场里「配置文件不存在」这种最常见的部署错误一句人话都没有。
	_, err := os.Stat(filePath)
	if err != nil {
		log.Fatalf("启动失败：配置文件 %s 不存在（-f 指的路径，或容器里没挂进去）", filePath)
	}
	yamlFile, err := ioutil.ReadFile(filePath)
	if err != nil {
		log.Fatalf("启动失败：读不了配置文件 %s：%v", filePath, err)
	}
	expanded, missing := expandEnv(string(yamlFile))
	if len(missing) > 0 {
		log.Fatalf("启动失败：这些环境变量没给值 → %s。凭据一律不入库，起服务前显式设好（清单见 README 部署段）",
			strings.Join(missing, ", "))
	}
	c := new(conf)
	err = yaml.Unmarshal([]byte(expanded), &c)
	if err != nil {
		log.Fatalf("启动失败：%s 解析不了：%v", filePath, err)
	}
	log.Printf("load conf success")
	// 绑定到外部可以访问的变量中
	Server = &c.Svc
	Database = &c.DB
	Redis = &c.RedisConfig
	Jwt = &c.Jwt
	XxlJob = &c.XxlJob
	LogConfig = &c.LogConfig
	UserPassword = &c.UserPassword
}
