<!-- agents: scope=admin parent= -->
# admin/ — 示例与脚手架代码

`admin/demo/single/{main,cate}` 是代码生成器产出的样例模块，形状与 `modules/` 完全相同：
`api.go` + `model.go` + `router.go` + `func Init(e *gin.Engine)`，同样必须在
`app/admin/router.go` 里登记。`scope=modules`

规则与差异：

- 这里的东西**不会被当真**：示例代码可以脏，但入口必须挂对——否则模块对账域
  出现「有的注册有的没注册」的噪声，MOD001 就废了。
- 新增示例前先确认它要不要进 `vben-go.sql` 的样例表；样例表结构变更走
  `.harness/memory/decisions.md` 记录，别静默改。
- 想改真正业务，去 `modules/`，不要往这里加。
