# 从python镜像开始构建
FROM python:3.10-alpine
# 注释标签
LABEL maintainer='peiyu'
LABEL description='Fastapi project'

# 创建/app目录并切换到该目录下
WORKDIR /app
# 拷贝代码到镜像中、拷贝文件到镜像中
COPY . .

# 安装必要的库
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \
    apk update && \
    apk upgrade && \
    apk add --no-cache tzdata mariadb-dev gcc libc-dev && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip && \
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && \
    chmod 755 ./entrypoint.sh \

# 创建日志挂载点避免容器越来越大
VOLUME /app/logs/

# 挂载端口，非端口映射，只是说明该镜像的挂载端口
EXPOSE 8000

# 启动容器后会执行entrypoint.sh的命令
ENTRYPOINT [ "./entrypoint.sh" ]
