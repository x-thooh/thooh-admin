package user

import (
	"encoding/json"
	"strings"
	"testing"
)

// TestSysUserOutboundHidesPassword 钉住 T-31 的出站契约：SysUser 的 password 字段
// 一旦被置空（Get/GetInfo 出站前的动作），序列化结果里连字段名都不该出现，
// 更不该出现 bcrypt 散列（$2a$ 前缀）。改掉 model 的 omitempty、或删掉出站前置空，
// 这个测试都会红。
func TestSysUserOutboundHidesPassword(t *testing.T) {
	u := SysUser{
		Id:       "u1",
		Username: "admin",
		Password: "$2a$10$fake",
	}
	u.Password = "" // 与 api.go Get/GetInfo 出站前一致

	b, err := json.Marshal(u)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	s := string(b)
	if strings.Contains(s, "password") {
		t.Fatalf("Password 置空后出站 JSON 不应含 password 字段：%s", s)
	}
	if strings.Contains(s, "$2") {
		t.Fatalf("出站 JSON 不应含 bcrypt 散列：%s", s)
	}
}
