# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：models
@Time ：2025/8/11 10:54
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""

from apiTest.apiCase.models import ApiCase
from apiTest.apiSuite.models import ApiTestSuite

from tortoise import fields, models


class ApiTaskRunRecord(models.Model):
    """测试计划运行记录表"""
    id = fields.IntField(pk=True, description="套件记录id", max_length=1000)
    project = fields.ForeignKeyField("models.Project", related_name="api_task_records", description="所属项目")
    task = fields.ForeignKeyField("models.ApiTask", related_name="api_task_records", description="执行的任务")
    env = fields.JSONField(description="执行环境", default=dict)
    start_time = fields.DatetimeField(auto_now_add=True, description="开始执行时间")
    duration = fields.FloatField(description="执行时间", default=0)
    status = fields.CharField(max_length=255, description="运行状态",
                              choices=[("等待执行", "等待执行"), ("执行完成", "执行完成"), ("执行中", "执行中")],
                              default="执行中")
    all = fields.IntField(description="总用例数", default=0)
    run_all = fields.IntField(description="执行用例数", default=0)
    no_run = fields.IntField(description="未执行用例数", default=0)
    success = fields.IntField(description="成功用例数", default=0)
    pass_rate = fields.FloatField(description="通过率", default=0)
    task_log = fields.JSONField(description="任务执行日志", default=list)
    fail = fields.IntField(description="失败用例数", default=0)
    error = fields.IntField(description="错误用例数", default=0)
    skip = fields.IntField(description="跳过用例数", default=0)
    username = fields.CharField(max_length=50, description="创建人")

    class Meta:
        table = "api_task_record"
        table_description = "测试计划运行记录"


class ApiSuiteRunRecord(models.Model):
    """测试套件运行记录表"""
    id = fields.IntField(pk=True, description="记录id", max_length=1000)
    suite = fields.ForeignKeyField("models.ApiTestSuite", related_name="api_suite_records", description="执行的套件")
    task_records = fields.ForeignKeyField("models.ApiTaskRunRecord", related_name="api_suite_records",
                                          description="关联的运行任务记录", null=True, blank=True)
    status = fields.CharField(max_length=255, description="运行状态",
                              choices=[("等待执行", "等待执行"), ("执行中", "执行中"), ("执行完成", "执行完成")],
                              default="执行中")
    all = fields.IntField(description="总用例数", default=0)
    run_all = fields.IntField(description="执行用例数", default=0)
    no_run = fields.IntField(description="未执行用例数", default=0)
    success = fields.IntField(description="成功用例数", default=0)
    fail = fields.IntField(description="失败用例数", default=0)
    error = fields.IntField(description="错误用例数", default=0)
    skip = fields.IntField(description="跳过用例数", default=0)
    start_time = fields.DatetimeField(auto_now_add=True, description="开始执行时间")
    duration = fields.FloatField(description="执行时间", default=0)
    suite_log = fields.JSONField(description="套件执行日志", default=list)
    pass_rate = fields.FloatField(description="通过率", default=0)
    env = fields.JSONField(description="执行环境", default=dict, null=True, blank=True)
    username = fields.CharField(max_length=50, description="创建人")

    class Meta:
        table = "api_suite_record"
        table_description = "测试套件运行记录"


class ApiCaseRunRecord(models.Model):
    """测试用例运行记录表"""
    id = fields.IntField(pk=True, description="用例记录id", max_length=1000)
    case = fields.ForeignKeyField("models.ApiCase", related_name="api_case_records", description="执行的用例")
    suite_records = fields.ForeignKeyField("models.ApiSuiteRunRecord", related_name="api_case_records",
                                           description="关联的运行套件记录", null=True, blank=True, default=None)
    status = fields.CharField(max_length=255, description="运行状态",
                              choices=[("success", "执行成功"), ("fail", "执行失败"),
                                       ("error", "执行错误"), ("skip", "跳过执行"), ("no_run", "未执行"),
                                       ("running", "执行中")], default="running")
    run_info = fields.JSONField(description="用例执行详情", default=dict)
    start_time = fields.DatetimeField(auto_now_add=True, description="开始执行时间")
    env = fields.JSONField(description="执行环境", default=dict)
    username = fields.CharField(max_length=50, description="创建人")

    class Meta:
        table = "api_case_record"
        table_description = "测试用例运行记录"


if __name__ == '__main__':
    pass
