#!/bin/sh

# 执行数据库迁移
aerich init -t common.settings.TORTOISE_ORM
aerich init-db
if [ $? -ne 0 ];then
    echo '数据库连接失败重启'
    exit 1
fi

# 启动gunicorn服务
gunicorn main:app -c gunicorn.py
