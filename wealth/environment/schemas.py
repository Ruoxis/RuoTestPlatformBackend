from datetime import datetime
from typing import Dict
from pydantic import BaseModel, Field


class EnvironmentSchemas(BaseModel):
    """环境列表的模型类"""
    id: int = Field(description="环境id")
    name: str = Field(description="环境名称")
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")
    host: str = Field(description="环境地址")
    global_vars: dict = Field(description="全局变量", default_factory=dict)
    project_id: int = Field(description="所属项目")
    username: str = Field(description="创建人")


class AddEnvironmentForm(BaseModel):
    """创建测试环境表单"""
    project_id: int = Field(description="所属项目")
    name: str = Field(description="环境名称")
    host: str = Field(description="环境地址")
    global_vars: Dict = Field(description="全局变量", default_factory=dict)
    username: str = Field(description="创建人")


class UpdateEnvironmentForm(BaseModel):
    """修改测试环境表单"""
    name: str | None = Field(default=None, description="环境名称")
    host: str | None = Field(default=None, description="环境地址")
    global_vars: Dict | None = Field(default=None, description="全局变量")
