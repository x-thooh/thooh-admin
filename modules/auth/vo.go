package auth

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
