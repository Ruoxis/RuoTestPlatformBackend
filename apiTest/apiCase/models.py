# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：mdels
@Time ：2025/7/10 14:13
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""

from common.src.unit.method_tools import EnumBase
from tortoise import fields, models


class CaseType(EnumBase):
    """用例类型枚举"""
    PERFORMANCE = "performance", "性能"
    NORMAL = "normal", "普调"
    DEBUG = "debug", "调试"


class ApiMethod(EnumBase):
    """接口请求方法枚举"""
    GET = "get", "GET"
    POST = "post", "POST"
    PUT = "put", "PUT"
    DELETE = "delete", "DELETE"


class RequestBodyType(EnumBase):
    """请求体类型枚举"""
    FORM = "form", "表单"
    JSON = "json", "JSON"
    NONE = "none", "无"
    RAW = "raw", "原始"
    PARAMS = "params", "参数"
    URLENCODED = "urlencoded", "URL编码"


class AssertType(EnumBase):
    """断言类型枚举"""
    REGEX = "regex", "正则匹配"
    JSON = "json", "JSON断言"
    TEXT = "text", "文本断言"


class ApiInfo(models.Model):
    """接口信息"""
    id = fields.IntField(pk=True, description="接口id", max_length=100)
    api_name = fields.CharField(max_length=100, description="接口名称")
    api_desc = fields.CharField(max_length=100, description="接口描述", null=True, blank=True)
    api_module = fields.CharField(max_length=100, description="接口模块", null=True, blank=True)
    api_method = fields.CharEnumField(max_length=30,
                                      enum_type=ApiMethod,
                                      default=ApiMethod.GET,
                                      description="接口请求方法")
    api_url = fields.CharField(max_length=100, description="接口路由")
    api_body_type = fields.CharEnumField(max_length=30,
                                         enum_type=RequestBodyType,
                                         default=RequestBodyType.NONE,
                                         description="请求体类型")
    api_status = fields.BooleanField(default=True, description="接口状态")
    request_data = fields.JSONField(description="请求参数", default=list, null=True, blank=True)
    request_headers = fields.JSONField(description="请求头", default=list, null=True, blank=True)
    variables = fields.JSONField(description="全局变量", default=list, null=True, blank=True)
    project = fields.ForeignKeyField(model_name="models.Project",  # 使用字符串引用，避免循环导入
                                     related_name="api_info",  # 反向查询名称
                                     description="关联项目",
                                     on_delete=fields.CASCADE  # 项目删除时级联删除用例
                                     )
    create_user = fields.ForeignKeyField(model_name="models.User",  # 使用字符串引用，避免循环导入
                                         related_name="api_infos_created_user",  # 反向查询名称
                                         description="创建人",
                                         db_column="create_user",  # 明确指定数据库列名
                                         on_delete=fields.CASCADE  # 项目删除时级联删除用例
                                         )
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_user = fields.ForeignKeyField(model_name="models.User",  # 使用字符串引用，避免循环导入
                                         related_name="api_infos_update_user",  # 反向查询名称
                                         description="最后修改人",
                                         db_column="update_user",  # 明确指定数据库列名
                                         on_delete=fields.CASCADE  # 项目删除时级联删除用例
                                         , null=True
                                         )
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "api_info"
        table_description = "接口信息"
        ordering = ["-create_time"]  # 按创建时间降序排列


class ApiCase(models.Model):
    id = fields.IntField(pk=True, description="用例id", max_length=100)
    case_name = fields.CharField(max_length=100, description="用例名称")
    case_desc = fields.CharField(max_length=100, description="用例描述", null=True)
    case_module = fields.CharField(max_length=100, description="用例模块", null=True)
    case_type = fields.CharEnumField(max_length=50,
                                     enum_type=CaseType, default=CaseType.NORMAL, description="用例类型")
    project = fields.ForeignKeyField(model_name="models.Project",
                                     related_name="api_cases_project",  # 反向查询名称
                                     description="关联项目",
                                     on_delete=fields.CASCADE  # 项目删除时级联删除用例
                                     )

    case_status = fields.BooleanField(default=True, description="用例状态")
    request_functions = fields.JSONField(description="前置步骤", default=list, null=True, blank=True)
    api = fields.ForeignKeyField(model_name="models.ApiInfo",  # 使用字符串引用，避免循环导入
                                 related_name="api_cases_api",  # 反向查询名称
                                 description="关联接口",
                                 on_delete=fields.CASCADE  # 项目删除时级联删除用例
                                 )
    dependencies_case_id = fields.JSONField(description="依赖用例id", default=list, null=True, blank=True)
    request_data = fields.JSONField(description="请求参数", default=list, null=True, blank=True)
    request_headers = fields.JSONField(description="请求头", default=list, null=True, blank=True)
    variables = fields.JSONField(description="全局变量", default=list, null=True, blank=True)
    response_functions = fields.JSONField(description="后置步骤", default=list, null=True, blank=True)
    assert_data = fields.JSONField(description="断言数据", default=list, null=True, blank=True)

    create_user = fields.ForeignKeyField(model_name="models.User",  # 使用字符串引用，避免循环导入
                                         related_name="api_cases_created_user",  # 反向查询名称
                                         description="创建人",
                                         db_column="create_user",  # 明确指定数据库列名
                                         on_delete=fields.CASCADE  # 项目删除时级联删除用例
                                         )
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_user = fields.ForeignKeyField(model_name="models.User",  # 使用字符串引用，避免循环导入
                                         related_name="api_cases_update_user",  # 反向查询名称
                                         description="最后修改人",
                                         db_column="update_user",  # 明确指定数据库列名
                                         on_delete=fields.CASCADE  # 项目删除时级联删除用例
                                         , null=True
                                         )
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "api_cases"
        table_description = "接口测试用例"
        ordering = ["-create_time"]  # 按创建时间降序排列


if __name__ == '__main__':
    pass
    # 创建用例
