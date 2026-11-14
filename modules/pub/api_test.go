package pub

import (
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestCurrentUserId(t *testing.T) {
	c, _ := gin.CreateTestContext(httptest.NewRecorder())
	c.Set("userId", "u2")
	got, ok := currentUserId(c)
	if !ok || got != "u2" {
		t.Fatalf("got %q ok=%v", got, ok)
	}
}

// 未登录：正常返回失败 JSON，不 panic。
func TestCurrentUserIdMissingReturnsFail(t *testing.T) {
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	if _, ok := currentUserId(c); ok {
		t.Fatal("expected !ok")
	}
	if !strings.Contains(w.Body.String(), "未登录") {
		t.Fatalf("body: %s", w.Body.String())
	}
}

// 菜单与参与者 SQL 必须按用户的角色关联过滤，不同角色才会拿到不同集合。
func TestSQLFilteredByRole(t *testing.T) {
	for _, q := range []string{userMenuSQL, userActorSQL} {
		if !strings.Contains(q, "sys_role_actor") || !strings.Contains(q, "aid=?") {
			t.Fatalf("missing role filter: %s", q)
		}
	}
	if !strings.Contains(userMenuSQL, "sys_role_menu") {
		t.Fatal("menu SQL must join sys_role_menu")
	}
}
