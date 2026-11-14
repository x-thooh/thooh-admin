package bitx

import (
	"database/sql/driver"
	"fmt"
	"reflect"
)

// Str 用于 dump 里的 bit(1) 列，同时保持 RuoYi 的字符串语义。
//
// WHY: 两边的口径是反的 —— dump 存 b'1' 表示「可用 / 显示 / 缓存」，而 RuoYi 的
// status/visible/isCache 用 "0" 表示同一件事。直接把 string 塞进 bit(1) 会得到
// 1406 Data too long（浏览器新增角色实测）；读出来则是 []byte{1}，扫不进 string。
// 这个类型在 Scan/Value 两处各翻一次，业务代码里的 `== "0"` 一行都不用改。
type Str string

// Scan 读库：bit 1 → "0"（正常/显示），bit 0 → "1"（停用/隐藏）
func (b *Str) Scan(value interface{}) error {
	if value == nil {
		*b = ""
		return nil
	}
	switch v := value.(type) {
	case []byte:
		if len(v) > 0 && v[0] != 0 {
			*b = "0"
		} else {
			*b = "1"
		}
	case int64:
		if v != 0 {
			*b = "0"
		} else {
			*b = "1"
		}
	case bool:
		if v {
			*b = "0"
		} else {
			*b = "1"
		}
	case string:
		// 已经是 "0"/"1" 的直接用
		*b = Str(v)
	default:
		rv := reflect.ValueOf(value)
		switch rv.Kind() {
		case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
			if rv.Int() != 0 {
				*b = "0"
			} else {
				*b = "1"
			}
		case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
			if rv.Uint() != 0 {
				*b = "0"
			} else {
				*b = "1"
			}
		default:
			return fmt.Errorf("无法将 %T 扫描为 bitx.Str", value)
		}
	}
	return nil
}

// Value 写库："0" → b'1'，其余（含 "1"、空串）→ b'0'
func (b Str) Value() (driver.Value, error) {
	if b == "0" {
		return int64(1), nil
	}
	return int64(0), nil
}
