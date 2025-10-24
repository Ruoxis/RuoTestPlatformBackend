# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：method_tools
@Time ：2025/7/9 8:41
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 测试方法工具类
"""
from enum import Enum
from fastapi import HTTPException, status


class MethodTools:
    @staticmethod
    def format_phone_smart(phone):
        """
        格式化手机号
        """
        phone = str(phone).strip()
        if not phone.isdigit():
            raise ValueError("必须为数字")

        # 已有1开头则直接补0，否则添加1再补0
        if phone.startswith('1'):
            return phone.ljust(11, '0')
        else:
            return ('1' + phone).ljust(11, '0')


class EnumBase(Enum):
    """枚举基类"""

    def __new__(cls, value, label):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.label = label
        return obj


class ValidatedError(Exception):
    """校验错误类"""

    def __init__(self, detail: str, status_code: int = 422):
        self.detail = detail
        self.status_code = status_code


if __name__ == '__main__':
    # import asyncio
    # asyncio.run(main())
    pass
