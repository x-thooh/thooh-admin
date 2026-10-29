package mysql

import (
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"

	"github.com/x-thooh/thooh-admin/common/config"
)

const testPassword = "sesame-for-test-only"

// 先占一个端口再放开：回环上的空闲端口立刻 ECONNREFUSED，比硬编码端口号确定
func closedPort(t *testing.T) string {
	t.Helper()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("占空闲端口失败：%v", err)
	}
	port := strconv.Itoa(ln.Addr().(*net.TCPAddr).Port)
	ln.Close()
	return port
}

func loadTestConfig(t *testing.T, port string) {
	t.Helper()
	file := filepath.Join(t.TempDir(), "config.yaml")
	text := "database:\n" +
		"  primary:\n" +
		"    host: 127.0.0.1\n" +
		"    port: \"" + port + "\"\n" +
		"    username: thooh\n" +
		"    password: " + testPassword + "\n" +
		"    dbname: thooh-go\n" +
		"  secondary:\n" +
		"    enabled: false\n" +
		"  max_idle_conn: 1\n" +
		"  max_open_conn: 1\n"
	if err := os.WriteFile(file, []byte(text), 0o600); err != nil {
		t.Fatalf("写测试配置失败：%v", err)
	}
	config.InitAppConfig(file)
}

func TestConnectMysqlFailureNamesTargetAndHidesPassword(t *testing.T) {
	port := closedPort(t)
	loadTestConfig(t, port)
	_connect = nil

	err := connectMysql()
	if err == nil {
		t.Fatal("连不上的库必须返回错误，不能把 nil 连接交给调用方")
	}
	msg := err.Error()
	for _, want := range []string{"主库", "thooh@127.0.0.1:" + port + "/thooh-go", "connection refused"} {
		if !strings.Contains(msg, want) {
			t.Errorf("错误消息里缺 %q，实际是：%s", want, msg)
		}
	}
	if strings.Contains(msg, testPassword) {
		t.Errorf("错误消息漏出了密码：%s", msg)
	}
	if _connect != nil {
		t.Error("连接失败后不该留下全局连接对象")
	}
}
