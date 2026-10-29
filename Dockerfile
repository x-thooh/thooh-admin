# 两段：编译也在容器里做。旧写法是 COPY 宿主上预先编好的 main，忘了 `go build -o main .`
# 就把上一个陈旧二进制烘进镜像，现场看不出来；客户机只需要 docker，不需要 Go。
FROM golang:1.26-alpine AS build
WORKDIR /src
# 依赖单独一层：改一行代码不必重下模块
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o /out/main .

FROM alpine:3.20
# tzdata：DSN 里 loc=Local，缺时区表会把本地时间读成 UTC；ca-certificates：https 外呼（xxl-job 等）
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /data/app
COPY --from=build /out/main ./main
# 前端产物与模板：routers.createRender() 启动时要读 web/{admin,mobile}/index.html 与 web/template/protocol.tmpl
# 缺一个就 panic: open web/admin/index.html: no such file or directory
COPY web ./web
# 配置不烘进镜像：值都在环境变量里（见 config.yaml 的形状与 docker-compose.yml 的挂载），
# 烘一份进去就是第二个事实源。
EXPOSE 8080
ENTRYPOINT ["./main"]
