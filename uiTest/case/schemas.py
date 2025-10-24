from datetime import datetime
from pydantic import BaseModel, Field


class CaseSchemas(BaseModel):
    """测试用例的模型定义"""
    id: int = Field(description="用例id")
    name: str = Field(description="用例名称")
    project_id: int = Field(description="所属项目")
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")
    steps: list = Field(description="用例执行步骤")
    level: str = Field(description="用例等级")
    username: str = Field(description="创建人")


class AddCaseForm(BaseModel):
    """创建测试用例表单"""
    name: str = Field(description="用例名称")
    level: str = Field(description="用例等级")
    project_id: int = Field(description="所属项目")
    steps: list = Field(description="用例执行步骤")
    username: str = Field(description="创建人")


class UpdateCaseForm(BaseModel):
    """修改测试用例表单"""
    name: str | None = Field(default=None, description="用例名称")
    level: str | None = Field(default=None, description="用例等级")
    steps: list | None = Field(default=None, description="用例执行步骤")
