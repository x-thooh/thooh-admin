# 基础镜像
FROM alpine:3.12
# 维护者
MAINTAINER RTHOOH
# docker build 时执行命令 - 创建目录
RUN mkdir -p "/data/app" \
&& ln -sf /dev/stdout /data/app/service.log
# 工作目录
WORKDIR "/data/app"
# 拷贝
COPY main /data/app/main
# 前端产物与模板：routers.createRender() 启动时要读 web/{admin,mobile}/index.html 与 web/template/protocol.tmpl
# 缺一个就 panic: open web/admin/index.html: no such file or directory
COPY web /data/app/web

# docker run 时执行命令
ENTRYPOINT ["./main"]
