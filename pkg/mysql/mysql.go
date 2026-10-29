package mysql

import (
	"fmt"
	"log"
	"os"
	"sync"
	"time"

	"github.com/x-thooh/thooh-admin/common/config"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var once sync.Once

// 定义数据库连接结构体
type connect struct {
	primaryDB *gorm.DB
	currentDB *gorm.DB
}

// 设置一个全局变量保存数据库连接
var _connect *connect

// target 是一个库的地址。dsn() 带密码，label() 不带——报错只用 label()：
// 这一行会进容器 stdout，可能被抓日志的链路留档。
type target struct {
	user     string
	password string
	host     string
	port     string
	dbName   string
}

func (t target) label() string {
	return t.user + "@" + t.host + ":" + t.port + "/" + t.dbName
}

func (t target) dsn() string {
	return t.user + ":" + t.password + "@tcp(" + t.host + ":" + t.port + ")/" + t.dbName +
		"?charset=utf8mb4&parseTime=True&loc=Local"
}

// open 建连接并配好连接池；错误里带库的地址与底层原因，不带密码
func open(role string, t target, newLogger logger.Interface) (*gorm.DB, error) {
	db, err := gorm.Open(mysql.Open(t.dsn()), &gorm.Config{Logger: newLogger})
	if err != nil {
		return nil, fmt.Errorf("%s %s 连不上：%w", role, t.label(), err)
	}
	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("%s %s 拿不到连接池：%w", role, t.label(), err)
	}
	sqlDB.SetMaxIdleConns(config.Database.MaxIdleConn)
	sqlDB.SetMaxOpenConns(config.Database.MaxOpenConn)
	sqlDB.SetConnMaxLifetime(time.Hour)
	return db, nil
}

// 连接 MySQL 数据库
func connectMysql() error {
	// 启用打印日志
	newLogger := logger.New(
		log.New(os.Stdout, "\r\n", log.LstdFlags), // io writer
		logger.Config{
			SlowThreshold: time.Second, // 慢 SQL 阈值
			LogLevel:      logger.Info, // 日志等级: Silent、Error、Warn、Info
			Colorful:      false,       // 禁用彩色打印
		},
	)

	p := config.Database.Primary
	primaryDB, err := open("主库", target{p.UserName, p.Password, p.Host, p.Port, p.DbName}, newLogger)
	if err != nil {
		return err
	}

	// 没开从库时「当前库」就是主库。旧写法把它留成 nil，
	// 于是 MysqlDb(true) 拿到一条 nil 连接，用的时候才炸。
	currentDB := primaryDB
	if config.Database.Secondary.Enabled {
		s := config.Database.Secondary
		secondaryDB, err := open("从库", target{s.UserName, s.Password, s.Host, s.Port, s.DbName}, newLogger)
		if err != nil {
			return err
		}
		currentDB = secondaryDB
	}

	_connect = &connect{
		primaryDB: primaryDB,
		currentDB: currentDB,
	}
	return nil
}

// SetPrimary 切换到主库
func SetPrimary() {
	if _connect != nil {
		_connect.currentDB = _connect.primaryDB
	}
}

/*使用
mysql.MysqlDb(true) 使用从数据库
mysql.MysqlDb() 使用主数据库
*/
// MysqlDb 获取当前使用的数据库连接
func MysqlDb(param ...bool) *gorm.DB {
	if _connect == nil {
		once.Do(func() {
			if err := connectMysql(); err != nil {
				// 连不上就退，不返回 nil。返回 nil 会被 gin 的 Recovery 咽成一个 500：
				// 进程活着、每个请求都 panic、日志里只有一串地址，比崩掉难查。
				log.Fatalf("启动失败：%v", err)
			}
		})
	}
	if len(param) > 0 {
		return _connect.currentDB
	}
	return _connect.primaryDB
}
