# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：models
@Time ：2025/9/22 11:53
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from enum import IntEnum

from tortoise import fields, models


class TaskType(IntEnum):
    """任务类型"""
    Order = 0
    Area = 1
    Tag = 2
    ToB = 3
    ToC = 4


class ToolsTask(models.Model):
    """项目模块"""
    id = fields.IntField(pk=True, description="任务id", max_length=100, auto_increment=True)
    cronjob_type = fields.IntEnumField(enum_type=TaskType, default=TaskType.UI, description="任务类型")
    name = fields.CharField(max_length=255, description="模块名称")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    project = fields.ForeignKeyField("models.Project", related_name="module", description="所属项目")
    username = fields.CharField(max_length=50, description="创建人")

    def __str__(self):
        return self.name

    class Meta:
        table = "module"
        table_description = "项目模块"


if __name__ == '__main__':
    pass
