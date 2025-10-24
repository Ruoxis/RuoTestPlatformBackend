# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：schemas
@Time ：2025/7/10 14:15
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, validator, computed_field
from common.factory_pattern import AsyncValidatedModel
from common.src.unit.method_tools import ValidatedError
from wealth.project.models import Project
from auth.user.models import User
from .models import ApiMethod, RequestBodyType, CaseType  # 新增导入 ApiInfo 和 ApiCase


class ApiInfoSchema(BaseModel):
    """接口信息的模型定义"""
    id: int = Field(description="接口id")
    api_name: str = Field(description="接口名称")
    api_desc: str | None = Field(description="接口描述")
    api_module: str | None = Field(description="接口模块")
    api_method: str = Field(description="接口请求方法", default=ApiMethod.GET)
    api_url: str = Field(description="接口路由")
    api_body_type: str = Field(description="请求体类型", default=RequestBodyType.NONE)
    api_status: bool = Field(description="接口状态")
    request_headers: List[dict] | None = Field(description="请求头")
    variables: List[dict] | None = Field(description="全局变量")
    request_data: List[dict] | None = Field(description="请求参数")
    project_id: int = Field(description="所属项目")
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
        用法: schema = await ApiInfoSchema.from_orm_with_relations(api_info)
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
        from_attributes = True  # 允许使用from_orm_with_relations方法
        arbitrary_types_allowed = True  # 允许任意类型


class ApiInfoList(BaseModel):
    """接口信息列表的模型定义"""
    data: List[ApiInfoSchema] = Field(description="接口信息列表")
    total: int = Field(description="接口总数")


class AddApiInfoForm(AsyncValidatedModel):
    """接口信息表单"""
    api_name: str = Field(description="接口名称")
    api_desc: str | None = Field(default=None, description="接口描述")
    api_module: str | None = Field(description="接口模块")
    api_method: str = Field(description="接口请求方法", default=ApiMethod.GET)
    api_url: str = Field(description="接口路由")
    api_body_type: str = Field(description="请求体类型", default=RequestBodyType.NONE)
    api_status: bool = Field(description="接口状态", default=True)
    request_data: List[dict] = Field(description="请求参数")
    request_headers: List[dict] | None = Field(description="请求头", default=list)
    variables: List[dict] | None = Field(description="全局变量", default=list)
    project_id: int = Field(description="所属项目")
    create_user_id: int | None = Field(description="创建人")

    @validator('api_method')
    def validate_api_method_format(cls, v):
        """接口方法验证"""
        try:
            method = ApiMethod(v)  # 尝试通过值构造枚举
        except Exception:
            raise ValidatedError(f"(api_method:{v})不是有效值")
        return method.value

    @validator('api_body_type')
    def validate_api_body_type_format(cls, v):
        """接口数据体类型验证"""
        try:
            method = RequestBodyType(v)  # 尝试通过值构造枚举
        except Exception:
            raise ValidatedError(f"(api_body_type:{v})不是有效值")
        return method.value

    async def async_validate(self):
        """其他验证（异步）"""
        project = await Project.get_or_none(id=self.project_id)
        if not project:
            raise ValidatedError(f"创建&更新接口信息失败：传入的项目id“{self.project_id}”不存在")
        create_user = await User.get_or_none(id=self.create_user_id)
        if not create_user:
            raise ValidatedError(f"创建&更新接口信息失败：传入的用户id“{self.create_user_id}”不存在")
        return self


class ApiInfoStatusForm(BaseModel):
    """接口信息表单"""
    api_status: bool = Field(description="接口状态", default=True)
    update_user_id: int | None = Field(description="最后更新人", default=None)


class UpdateApiInfoForm(AddApiInfoForm):
    """接口信息表单"""
    update_user_id: int | None = Field(description="最后更新人", default=None)

    async def async_validate(self):
        """异步验证"""
        # 先调用父类验证
        await super().async_validate()
        # 验证更新用户
        update_user = await User.get_or_none(id=self.update_user_id)
        if not update_user:
            raise ValidatedError(f"更新用户id“{self.update_user_id}”不存在")
        return self


class ApiCaseSchema(BaseModel):
    """接口测试用例的模型定义"""
    id: int = Field(description="用例ID")
    case_name: str = Field(description="用例名称")
    case_desc: str | None = Field(default=None, description="用例描述")
    case_module: str | None = Field(description="接口模块")
    project_id: int = Field(description="所属项目")
    case_type: str = Field(description="用例类型", default=CaseType.NORMAL)
    case_status: bool = Field(description="用例状态", default=True)
    dependencies_case_id: List | None = Field(description="关联用例id")
    request_functions: List[dict] | None = Field(description="前置步骤")
    api_id: int | None = Field(description="关联用例id")
    request_headers: List[dict] | None = Field(description="请求头")
    variables: List[dict] | None = Field(description="全局变量")
    request_data: List[dict] | None = Field(description="请求参数")
    response_functions: List[dict] | None = Field(description="后置步骤")
    assert_data: List[dict] = Field(description="预期结果")
    create_user_id: int = Field(description="创建人")
    create_time: datetime = Field(description="创建时间")
    update_user_id: int | None = Field(default=None, description="更新人")
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

    @computed_field
    @property
    def api_method(self) -> str | None:
        """动态获取关联接口的请求方法"""
        try:
            if hasattr(self, "_api"):
                return self._api.api_method.value if self._api.api_method else None
        except Exception as e:
            return None

    @computed_field
    @property
    def api_url(self) -> str | None:
        """动态获取关联接口的路由"""
        try:
            return getattr(self._api, "api_url", None) if hasattr(self, "_api") else None
        except Exception as e:
            return None

    @computed_field
    @property
    def api_name(self) -> str | None:
        """动态获取关联接口的名称"""
        try:
            return getattr(self._api, "api_name", None) if hasattr(self, "_api") else None
        except Exception as e:
            return None

    @computed_field
    @property
    def api_body_type(self) -> str | None:
        """动态获取关联接口的请求体类型"""
        try:
            if hasattr(self, "_api"):
                return self._api.api_body_type.value if self._api.api_body_type else None
        except Exception as e:
            return None

    @computed_field
    @property
    def api_status(self) -> str | None:
        """动态获取关联接口的请求体类型"""
        try:
            if hasattr(self, "_api"):
                return getattr(self._api, "api_status", None) if hasattr(self, "_api") else None
        except Exception as e:
            return None

    @classmethod
    async def from_orm_with_relations(cls, db_obj):
        """
        从ORM对象转换，自动注入关联对象
        用法: schema = await ApiInfoSchema.from_orm_with_relations(api_info)
        """
        schema = cls.model_validate(db_obj)
        if hasattr(db_obj, "project"):
            schema._project = db_obj.project
        if hasattr(db_obj, "create_user"):
            schema._create_user = db_obj.create_user
        if hasattr(db_obj, "update_user"):
            schema._update_user = db_obj.update_user
        # 处理关联的API信息
        if hasattr(db_obj, "api"):
            api = await db_obj.api.first()  # 使用first()获取第一个关联对象
            schema._api = api

        return schema

    @classmethod
    async def from_queryset(cls, queryset):
        """批量转换方法"""
        return [await cls.from_orm_with_relations(obj) for obj in queryset]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class CopyApiCaseForm(BaseModel):
    create_user_id: int = Field(description="创建人")


class AddApiCaseForm(AsyncValidatedModel):
    """创建接口测试用例表单"""
    project_id: int = Field(description="所属项目")
    case_name: str = Field(description="用例名称")
    case_desc: str | None = Field(default=None, description="用例描述")
    case_module: str | None = Field(description="接口模块")
    case_type: str = Field(description="用例类型", default=CaseType.NORMAL)
    case_status: bool = Field(description="用例状态", default=True)
    dependencies_case_id: List | None = Field(description="关联用例id", default=None)
    request_functions: List[dict] | None = Field(description="请求函数", default=list)
    api_id: int | None = Field(description="关联用例id")
    request_headers: List[dict] | None = Field(description="请求头")
    variables: List[dict] | None = Field(description="全局变量")
    request_data: List[dict] | None = Field(description="请求参数")
    response_functions: List[dict] | None = Field(description="响应函数", default=list)
    assert_data: List[dict] = Field(description="预期结果")
    create_user_id: int = Field(description="创建人")

    @validator('case_type')
    def validate_api_method_format(cls, v):
        """接口方法验证"""
        try:
            method = CaseType(v)  # 尝试通过值构造枚举
        except Exception:
            raise ValidatedError(f"(case_type:{v})不是有效值")
        return method.value

    async def async_validate(self):
        """其他验证（异步）"""
        project = await Project.get_or_none(id=self.project_id)
        if not project:
            raise ValidatedError(f"创建&更新接口用例失败：传入的项目id“{self.project_id}”不存在")
        create_user = await User.get_or_none(id=self.create_user_id)
        if not create_user:
            raise ValidatedError(f"创建&更新接口用例失败：传入的用户id“{self.create_user_id}”不存在")
        return self


class UpdateApiCaseForm(AddApiCaseForm):
    """修改接口测试用例表单"""
    update_user_id: int | None = Field(default=None, description="更新人ID")

    async def async_validate(self):
        """异步验证"""
        # 先调用父类验证
        await super().async_validate()
        # 验证更新用户
        update_user = await User.get_or_none(id=self.update_user_id)
        if not update_user:
            raise ValidatedError(f"更新用户id“{self.update_user_id}”不存在")

        return self


class ApiCaseList(BaseModel):
    """接口信息列表的模型定义"""
    data: List[ApiCaseSchema] = Field(description="接口信息列表")
    total: int = Field(description="接口总数")


class ApiCaseStatusForm(BaseModel):
    """接口信息表单"""
    case_status: bool = Field(description="接口状态", default=True)
    update_user_id: int | None = Field(description="最后更新人", default=None)


# 接口信息调试接口
class ApiInfoDebugSchema(BaseModel):
    api_id: int = Field(description="用例ID")
    env_id: int = Field(description="环境ID")


class ApiCaseDebugSchema(BaseModel):
    case_id: int = Field(description="用例ID")
    env_id: int = Field(description="环境ID")


class ApiDebugResponse(BaseModel):
    """ 接口调试响应 """
    basicInfo: dict = Field(description="基本信息")
    headers: List[dict] = Field(description="请求头")
    body: dict = Field(description="响应体")


class FunListResponse(BaseModel):
    """ 函数字典 """
    before_fun: List[dict] | None = Field(description="前置函数")
    after_fun: List[dict] | None = Field(description="后置函数")
    public_fun: List[dict] | None = Field(description="公共函数")


if __name__ == '__main__':
    pass
