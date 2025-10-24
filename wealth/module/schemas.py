from datetime import datetime
from pydantic import BaseModel, Field


class ModuleSchemas(BaseModel):
    """测试模块的模型类"""
    id: int = Field(description="模块id")
    name: str = Field(description="模块名称")
    project_id: int = Field(description="所属项目")
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")
    username: str = Field(description="创建人")


class AddModuleForm(BaseModel):
    """创建测试模块表单"""
    project_id: int = Field(description="所属项目")
    name: str = Field(description="模块名称")
    username: str = Field(description="创建人")


class UpdateModuleForm(BaseModel):
    """修改测试模块表单"""
    name: str | None = Field(default=None, description="模块名称")
