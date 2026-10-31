package auth

import (
	"github.com/x-thooh/thooh-admin/common/json/timex"
	"github.com/x-thooh/thooh-admin/modules/sys/org"
)

type LoginVo struct {
	AccessToken string `json:"access_token"`
	ExpireIn    int64  `json:"expire_in"`
}

// Session 是登录态在 redis 里的那份值。id 一律是 dump 的 varchar(36) 口径；
// 鉴权中间件只按键的存在判断「这次 token 还在不在」，取字段是在线用户列表的事。
type Session struct {
	TokenId       string `json:"tokenId"`
	UserId        string `json:"userId"`
	UserName      string `json:"userName"`
	NickName      string `json:"nickName"`
	OrgId         string `json:"orgId"`
	OrgName       string `json:"orgName"`
	Ipaddr        string `json:"ipaddr"`
	LoginLocation string `json:"loginLocation"`
	Browser       string `json:"browser"`
	Os            string `json:"os"`
	LoginTime     int64  `json:"loginTime"`
}

// UserVo 是 /getInfo 里 user 那一段。键名是 web/admin 与 web/mobile 读的那一套
// （userName/nickName/phonenumber/sex/avatar/userId），值来自 dump 口径的 sys_user：
// username→userName、name→nickName、monum→phonenumber、gender→sex。
// 一个都不带 password：T-31 记的就是旧实现把口令原样吐进列表接口。
type UserVo struct {
	UserId      string      `json:"userId"`
	UserName    string      `json:"userName"`
	NickName    string      `json:"nickName"`
	Phonenumber string      `json:"phonenumber"`
	Email       string      `json:"email"`
	Avatar      string      `json:"avatar"`
	Sex         string      `json:"sex"`
	CreateTime  timex.Time  `json:"createTime"`
	Dept        *org.SysOrg `json:"dept"`
}

// RouterVo / MetaVo 是 /getRouters 的响应形状，逐键照旧实现
// （app/admin/model/system/sysMenu.go 的 MenuVo/MetaVo，omitempty 的位置也一致）：
// web/admin 的 filterAsyncRouter 按 component=="Layout" 找布局、按 children 有无决定嵌套，
// 键名换了前端就白屏。
type RouterVo struct {
	Name       string     `json:"name"`
	Path       string     `json:"path,omitempty"`
	Hidden     bool       `json:"hidden"`
	Redirect   string     `json:"redirect,omitempty"`
	Component  string     `json:"component,omitempty"`
	Query      string     `json:"query,omitempty"`
	AlwaysShow bool       `json:"alwaysShow,omitempty"`
	Meta       MetaVo     `json:"meta"`
	Children   []RouterVo `json:"children,omitempty"`
}

type MetaVo struct {
	Title   string `json:"title"`
	Icon    string `json:"icon"`
	NoCache bool   `json:"noCache"`
	Link    string `json:"link,omitempty"`
}
