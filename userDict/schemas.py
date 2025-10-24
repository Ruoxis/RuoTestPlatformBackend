# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：schemas
@Time ：2025/7/24 18:00
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, validator
from common.factory_pattern import AsyncValidatedModel
from common.src.unit.method_tools import ValidatedError
from auth.user.models import User


class FunctionType(str, Enum):
    """函数类型枚举"""
    BEFORE = "before"
    AFTER = "after"
    PUBLIC = "public"
    ASSERTION = "assertion"
    OTHER = "other"
    DEFAULT = "default"


class FunctionDictBase(BaseModel):
    """函数字典模型基类"""
    id: int = Field(description="函数ID")
    dict_type: FunctionType = Field(default=FunctionType.DEFAULT, description="函数类型")
    dict_name: str = Field(description="函数字典名称")
    class_name: str = Field(description="函数类名")
    method_name: str = Field(description="函数名")
    params: List[dict] | None = Field(description="参数列表")
    fun_desc: str | None = Field(description="函数描述")
    status: bool = Field(default=True, description="函数状态")
    returns: str | None = Field(description="函数返回说明")
    is_inherited: bool = Field(default=False, description="是否继承")
    cite: str = Field(description="引用方式")
    update_time: datetime | None = Field(description="更新时间")

    async def from_queryset(cls, queryset):
        """批量转换方法"""
        return [await cls.from_orm_with_relations(obj) for obj in queryset]

    class Config:
        from_attributes = True  # 允许使用from_orm_with_relations方法
        arbitrary_types_allowed = True  # 允许任意类型


class FunctionDictList(BaseModel):
    """函数字典列表响应模型"""
    data: List[FunctionDictBase] = Field(description="函数列表")
    total: int = Field(description="总数")


class AddFunctionDictForm(AsyncValidatedModel):
    """添加函数字典表单"""
    fun_name: str = Field(description="函数名称")
    fun_desc: str = Field(description="函数描述")
    fun_type: str = Field(description="函数类型(before/after/public)")
    params: List[dict] = Field(description="参数列表")
    create_user_id: int = Field(description="创建人ID")

    @validator('fun_type')
    def validate_fun_type(cls, v):
        """验证函数类型"""
        try:
            func_type = FunctionType(v)
        except ValueError:
            raise ValidatedError(f"(fun_type:{v})不是有效值")
        return func_type.value

    async def async_validate(self):
        """异步验证"""
        user = await User.get_or_none(id=self.create_user_id)
        if not user:
            raise ValidatedError(f"创建用户ID {self.create_user_id} 不存在")
        return self


class UpdateFunctionDictForm(AddFunctionDictForm):
    """更新函数字典表单"""
    update_user_id: int | None = Field(description="更新人ID", default=None)

    async def async_validate(self):
        """异步验证"""
        await super().async_validate()
        if self.update_user_id:
            user = await User.get_or_none(id=self.update_user_id)
            if not user:
                raise ValidatedError(f"更新用户ID {self.update_user_id} 不存在")
        return self


if __name__ == '__main__':
    pass
