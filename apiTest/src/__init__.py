# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：__init__.py
@Time ：2025/7/10 14:10
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from fastapi import FastAPI
# db.py
from tortoise import Tortoise
from common import settings


async def init_db():
    """应用启动时调用一次"""
    await Tortoise.init(config=settings.TORTOISE_ORM)


async def close_db():
    """应用关闭时调用"""
    await Tortoise.close_connections()


def get_db():
    """获取已初始化的数据库连接"""
    return Tortoise.get_connection("default")


app = FastAPI()


@app.on_event("startup")
async def startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


if __name__ == '__main__':
    pass
