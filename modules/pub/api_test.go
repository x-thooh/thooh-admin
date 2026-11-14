package pub

import (
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestCurrentUserId(t *testing.T) {
	c, _ := gin.CreateTestContext(nil)
	c.Set("userId", "u2")
	if got := currentUserId(c); got != "u2" {
		t.Fatalf("got %q", got)
	}
}

func TestCurrentUserIdMissingPanics(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("expected panic")
		}
	}()
	c, _ := gin.CreateTestContext(nil)
	currentUserId(c)
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
