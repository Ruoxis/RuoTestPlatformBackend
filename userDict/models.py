# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：models
@Time ：2025/7/24 18:00
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from common.src.unit.method_tools import EnumBase
from tortoise import fields, models


class DictType(EnumBase):
    """字典类型枚举"""
    FUNCTION = "function", "函数"
    ASSERTION = "assertion", "断言"
    USER = "user", "用户"
    SYSTEM = "system", "系统"
    CUSTOM = "custom", "自定义"


class DictAttributes():
    """字典属性枚举json text """
    JSON = "json", "json"
    TEXT = "text", "text"


class FunctionDictType(EnumBase):
    """字典类型枚举after、before、public、其他"""
    AFTER = "after", "后置"
    BEFORE = "before", "前置"
    PUBLIC = "public", "公共"
    ASSERTION = "assertion", "断言"
    OTHER = "other", "其他"
    DEFAULT = "default", "默认"


class FunctionDict(models.Model):
    """函数字典"""
    id = fields.BigIntField(pk=True, description="字典id", max_length=100)
    dict_type = fields.CharEnumField(max_length=30, description="字典类型", enum_type=FunctionDictType,
                                     default=FunctionDictType.DEFAULT)
    dict_name = fields.CharField(max_length=100, description="函数调用名", unique=True)
    class_name = fields.CharField(max_length=100, description="函数类名")
    method_name = fields.CharField(max_length=100, description="函数名")
    params = fields.JSONField(description="函数参数", default=list, null=True, blank=True)
    fun_desc = fields.TextField(max_length=300, description="函数说明", null=True, blank=True)
    status = fields.BooleanField(default=True, description="字典状态")
    returns = fields.CharField(max_length=300, description="函数返回说明", null=True, blank=True)
    is_inherited = fields.BooleanField(default=False, description="是否继承")
    cite = fields.CharField(max_length=100, description="引用方式")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "function_dict"
        table_description = "函数字典"
        ordering = ["id"]


if __name__ == '__main__':
    pass
