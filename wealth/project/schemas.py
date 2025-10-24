from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class ProjectSchemas(BaseModel):
    """项目的模型类"""
    id: int = Field(description="项目id")
    name: str = Field(description="项目名称")
    user_id: int = Field(description="项目创建人id")
    # 时间在声明的时候要注意类型
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")
    username: str = Field(description="创建人")


class AddProjectForm(BaseModel):
    """添加项目表单"""
    name: str = Field(description="项目名称", max_length=20)


class UpdateProjectForm(BaseModel):
    """更新项目表单"""
    name: str = Field(description="项目名称", max_length=20)


class ProjectListSchemas(BaseModel):
    """项目列表的模型类"""
    total: int = Field(description="总数")
    data: List[ProjectSchemas] = Field(description="数据")
