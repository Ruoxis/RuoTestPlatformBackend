# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：schemas
@Time ：2025/8/18 7:57
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""

from pydantic import BaseModel, Field, validator, computed_field
from common.factory_pattern import AsyncValidatedModel
from common.src.unit.method_tools import ValidatedError
from typing import Optional, List
from wealth.project.models import Project
from datetime import datetime
from auth.user.models import User
from .models import ApiSuiteType


class ApiTestSuiteSchema(BaseModel):
    """测试套件的模型定义"""
    id: int = Field(description="套件ID")
    suite_name: str = Field(description="套件名称")
    suite_desc: str | None = Field(description="套件描述")
    suite_module: str | None = Field(description="所属模块")
    suite_status: bool = Field(description="套件状态")
    suite_setup_step: List[dict] | None = Field(description="套件前置步骤")
    suite_type: str = Field(description="套件类型")
    project_id: int = Field(description="关联项目")
    cases_order: List | None = Field(description="用例执行顺序")
    variables: List[dict] | None = Field(description="套件全局变量")
    config: dict | None = Field(description="套件配置")
    create_user_id: int = Field(description="创建人")
    create_time: datetime = Field(description="创建时间")
    update_user_id: int | None = Field(description="最后更新人")
    update_time: datetime | None = Field(description="更新时间")

    @computed_field
    @property
    def project_name(self) -> str:
        """动态获取项目返回数据名称"""
        try:
            return self._project.name if hasattr(self, "_project") else "未知项目"
        except Exception as e:
            return "未知项目"

    @computed_field
    @property
    def create_user_name(self) -> str:
        """动态获取创建人返回数据名称"""
        try:
            return self._create_user.username if hasattr(self, "_create_user") else "未知用户"
        except Exception as e:
            return "未知用户"

    @computed_field
    @property
    def update_user_name(self) -> Optional[str]:
        """动态获取更新人返回数据的名称"""
        try:
            return getattr(self._update_user, "username", None) if hasattr(self, "_update_user") else None
        except Exception as e:
            return None

    @classmethod
    async def from_orm_with_relations(cls, db_obj):
        """
        从ORM对象转换，自动注入关联对象
        用法: schema = await ApiTestSuiteSchema.from_orm_with_relations(api_suite)
        """
        schema = cls.model_validate(db_obj)
        if hasattr(db_obj, "project"):
            schema._project = db_obj.project
        if hasattr(db_obj, "create_user"):
            schema._create_user = db_obj.create_user
        if hasattr(db_obj, "update_user"):
            schema._update_user = db_obj.update_user
        return schema

    @classmethod
    async def from_queryset(cls, queryset):
        """批量转换方法"""
        return [await cls.from_orm_with_relations(obj) for obj in queryset]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ApiTestSuiteList(BaseModel):
    """测试套件列表的模型定义"""
    data: List[ApiTestSuiteSchema] = Field(description="测试套件列表")
    total: int = Field(description="套件总数")


class AddApiTestSuiteBaseForm(BaseModel):
    project_id: int = Field(description="关联项目")
    suite_name: str = Field(description="套件名称")
    suite_desc: str | None = Field(default=None, description="套件描述")
    suite_module: str | None = Field(description="所属模块")
    suite_status: bool = Field(description="套件状态", default=True)
    suite_type: str = Field(description="套件类型", default=ApiSuiteType.NORMAL)
    create_user_id: int = Field(description="创建人")


class AddApiTestSuiteForm(AsyncValidatedModel):
    """创建测试套件表单"""
    project_id: int = Field(description="关联项目")
    suite_name: str = Field(description="套件名称")
    suite_desc: str | None = Field(default=None, description="套件描述")
    suite_module: str | None = Field(description="所属模块")
    suite_status: bool = Field(description="套件状态", default=True)
    suite_type: str = Field(description="套件类型", default=ApiSuiteType.NORMAL)
    cases_order: List | None = Field(description="用例执行顺序", default=list)
    variables: List[dict] | None = Field(description="套件全局变量", default=list)
    suite_setup_step: List[dict] | None = Field(description="套件前置步骤", default=list)
    config: dict | None = Field(description="套件配置", default=dict)
    create_user_id: int = Field(description="创建人")

    @validator('suite_type')
    def validate_suite_type_format(cls, v):
        """套件类型验证"""
        try:
            suite_type = ApiSuiteType(v)  # 尝试通过值构造枚举
        except Exception:
            raise ValidatedError(f"(suite_type:{v})不是有效值")
        return suite_type.value

    async def async_validate(self):
        """其他验证（异步）"""
        project = await Project.get_or_none(id=self.project_id)
        if not project:
            raise ValidatedError(f"创建&更新测试套件失败：传入的项目id‘{self.project_id}’不存在")
        create_user = await User.get_or_none(id=self.create_user_id)
        if not create_user:
            raise ValidatedError(f"创建&更新测试套件失败：传入的用户id‘{self.create_user_id}’不存在")
        return self


class UpdateApiTestSuiteForm(AddApiTestSuiteForm):
    """修改测试套件表单"""
    update_user_id: int | None = Field(default=None, description="更新人ID")

    async def async_validate(self):
        """异步验证"""
        # 先调用父类验证
        await super().async_validate()
        # 验证更新用户
        update_user = await User.get_or_none(id=self.update_user_id)
        if not update_user:
            raise ValidatedError(f"更新用户id‘{self.update_user_id}’不存在")
        return self


class ApiTestSuiteStatusForm(BaseModel):
    """测试套件状态表单"""
    suite_status: bool = Field(description="套件状态", default=True)
    update_user_id: int | None = Field(description="最后更新人", default=None)


class CopyApiTestSuiteForm(BaseModel):
    create_user_id: int = Field(description="创建人")


if __name__ == '__main__':
    pass
