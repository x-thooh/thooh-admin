package mysql

import (
	"testing"

	"gorm.io/gorm/logger"
)

func TestGormLogLevel(t *testing.T) {
	cases := map[string]logger.LogLevel{
		"debug": logger.Info, "DEBUG": logger.Info, "info": logger.Warn, "warn": logger.Warn,
		"error": logger.Error, "silent": logger.Silent, "": logger.Warn, "bogus": logger.Warn,
	}
	for in, want := range cases {
		if got := gormLogLevel(in); got != want {
			t.Errorf("gormLogLevel(%q)=%v want %v", in, got, want)
		}
	}
}
