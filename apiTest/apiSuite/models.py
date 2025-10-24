# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：mdels
@Time ：2025/7/10 14:15
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from tortoise import models, fields

from common.src.unit.method_tools import EnumBase

suite = {
    'username': 'test_user',
    'host': 'https://www.baidu.com',
    'task': [
        {'suite_id': None,
         'suite_name': '百度搜索',
         "variables": [
             {
                 "key": "path",
                 "value": "D:/sada/dsad/a.text",
                 "remarks": "文件路径"
             },
             {
                 "key": "store",
                 "value": "$<<depend_1_body:$.store>>",  # 直接依赖使用
                 "remarks": "用例依赖的响应体获取store",

                 "Aa": {
                     "key": "store",
                     "value": "$<<depend_1_body:$.store>>",  # josn嵌套依赖使用
                     "remarks": "用例依赖的响应体获取store"
                 }

             },
         ],
         'cases': [17],
         },
        {
            'suite_name': '百度搜索',  # 套件名称
            'suite_id': None,  # 套件id
            'cases': [16],  # 包含用例id
            'variables': [],  # 套件变量
        }
    ]
}


class ApiSuiteType(EnumBase):
    """用例类型枚举"""
    INTEGRATION = "integration", "集成测试"
    REGRESSION = "regression", "回归测试"
    SMOKE = "smoke", "冒烟测试"
    SECURITY = "security", "安全测试"
    PERFORMANCE = "performance", "性能测试"
    SANITY = "sanity", "专项验证"
    CI_CD = "ci_cd", "流水线专用"
    NORMAL = "normal", "普通测试"
    OTHER = "other", "其他"


class ApiTestSuite(models.Model):
    """测试套件"""
    id = fields.IntField(pk=True, description="套件ID")
    suite_name = fields.CharField(max_length=100, description="套件名称")
    project = fields.ForeignKeyField(model_name="models.Project", related_name="suites_project", description="关联项目",
                                     on_delete=fields.CASCADE)
    suite_module = fields.CharField(max_length=100, description="所属模块", null=True, blank=True)
    suite_desc = fields.CharField(max_length=200, description="套件描述", null=True, blank=True)
    suite_status = fields.BooleanField(default=True, description="套件状态")
    suite_type = fields.CharEnumField(max_length=50, enum_type=ApiSuiteType,  # 复用用例类型枚举
                                      default=ApiSuiteType.NORMAL, description="套件类型")
    suite_setup_step = fields.JSONField(description="套件前置步骤", default=list, null=True, blank=True)
    cases_order = fields.JSONField(description="用例执行顺序", default=list, null=True, blank=True)
    variables = fields.JSONField(description="套件全局变量", default=list, null=True, blank=True)
    config = fields.JSONField(description="套件配置", default=dict, null=True, blank=True,
                              help_text="如环境配置、超时设置等")

    create_user = fields.ForeignKeyField(model_name="models.User", related_name="suites_create_user",
                                         description="创建人",
                                         on_delete=fields.CASCADE)
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_user = fields.ForeignKeyField(model_name="models.User", related_name="suites_update_user",
                                         description="最后修改人",
                                         null=True)
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "api_test_suite"
        table_description = "测试套件"
        ordering = ["-create_time"]


if __name__ == '__main__':
    pass
