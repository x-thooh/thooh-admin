package config

import (
	"os"
	"reflect"
	"testing"
)

// 配置注入的四种形状各钉一条：给值、走默认、明写允许空、缺值点名。
// 第四条是这一层的存在理由——凭据不入库之后，「缺哪个」必须是第一条能被读懂的错误。
func TestExpandEnv(t *testing.T) {
	t.Setenv("THOOH_SET", "from-env")
	t.Setenv("THOOH_EMPTY", "")

	cases := []struct {
		name    string
		text    string
		want    string
		missing []string
	}{
		{"给值就换成值", "password: ${THOOH_SET}", "password: from-env", nil},
		{"没给值用冒号后的默认", "host: ${THOOH_UNSET:-127.0.0.1}", "host: 127.0.0.1", nil},
		{"明写空默认是允许空，不是缺值", "password: ${THOOH_UNSET:-}", "password: ", nil},
		{"环境变量存在但为空串仍算没给", "password: ${THOOH_EMPTY:-fallback}", "password: fallback", nil},
		{"缺必填要点名", "a: ${THOOH_A}\nb: ${THOOH_B:-}\nc: ${THOOH_A}", "a: ${THOOH_A}\nb: \nc: ${THOOH_A}", []string{"THOOH_A"}},
		{"注释里的示例不是引用", "port: 8080 # 语法 ${NAME} 必填\n", "port: 8080 # 语法 ${NAME} 必填\n", nil},
		{"值里的井号不算注释", "url: http://x/y#frag ${THOOH_SET}", "url: http://x/y#frag from-env", nil},
	}
	for _, c := range cases {
		got, missing := expandEnv(c.text)
		if got != c.want {
			t.Errorf("%s：展开成 %q，期望 %q", c.name, got, c.want)
		}
		if !reflect.DeepEqual(missing, c.missing) {
			t.Errorf("%s：缺值清单 %v，期望 %v", c.name, missing, c.missing)
		}
	}
}

// 展开只发生在读文件之后、解析之前，所以 os.ExpandEnv 那种「裸 $ 也吃」的语义
// 不能用在值上：密码里的 $ 会被吞掉，且一句报错都没有。
func TestBareDollarIsNotAReference(t *testing.T) {
	t.Setenv("PW", "swallowed")
	got, missing := expandEnv("password: pa$ssword\n")
	if got != "password: pa$ssword\n" || missing != nil {
		t.Fatalf("裸 $ 被当成引用了：%q / %v", got, missing)
	}
	if os.Getenv("PW") != "swallowed" {
		t.Fatal("夹具没设上环境变量")
	}
}
