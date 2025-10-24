# -*- coding: utf-8 -*-
from tortoise import models, fields

from enum import IntEnum


class TaskType(IntEnum):
    """任务类型"""
    UI = 0
    API = 1


class ApiTask(models.Model):
    """计划的模型类"""
    id = fields.IntField(pk=True, description="任务id", max_length=100, auto_increment=True)
    name = fields.CharField(max_length=255, description="任务名称")
    project = fields.ForeignKeyField("models.Project", related_name="api_tasks", description="所属项目")
    task_type = fields.IntEnumField(enum_type=TaskType, default=TaskType.API, description="任务类型", )
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    suites = fields.ManyToManyField("models.ApiTestSuite", related_name="api_tasks", default=[],
                                    description="任务中套件",
                                    null=True, blank=True)
    username = fields.CharField(max_length=50, description="创建人")

    class Meta:
        table = "api_task"
        table_description = "接口测试计划"
