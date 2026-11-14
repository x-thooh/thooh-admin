package system

// SysUserPost model：数据库字段
type SysUserPost struct {
	PostId string `json:"column:postId"`
	UserId string `json:"userId"`
}

// TableName 指定数据库表名称
func (SysUserPost) TableName() string {
	return "sys_post_actor"
}
