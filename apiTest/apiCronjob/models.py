from enum import IntEnum

from tortoise import fields, models


class TaskType(IntEnum):
    """任务类型"""
    UI = 0
    API = 1


class ApiCronjob(models.Model):
    """任务表"""
    id = fields.BigIntField(pk=True, description="任务id", max_length=20, auto_increment=True)
    name = fields.CharField(max_length=50, description="任务名称")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建日期")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    project = fields.ForeignKeyField("models.Project", related_name="api_cronjob", description="所属项目")
    env = fields.ForeignKeyField("models.Environment", related_name="api_cronjob", description="执行环境")
    task = fields.ForeignKeyField("models.ApiTask", related_name="api_cronjob", description="执行的测试计划")
    state = fields.BooleanField(default=True, description="是否启用")
    run_type = fields.CharField(max_length=10, choices=['Interval', 'date', 'crontab'], description="任务类型")
    interval = fields.BigIntField(default=60, description="执行间隔时间")
    cronjob_type = fields.IntEnumField(enum_type=TaskType, default=TaskType.API, description="任务类型")
    date = fields.DatetimeField(default='2025-12-01 00:00:00', description="指定执行的事件")
    crontab = fields.JSONField(default={'minute': '30', 'hour': '*', 'day': '*', 'month': '*', 'day_of_week': '*'},
                               description="周期性任务规则")

    username = fields.CharField(max_length=50, description="创建人")

    class Meta:
        table = "api_cronjob"
        table_description = "定时任务"
