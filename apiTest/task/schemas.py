from datetime import datetime
from pydantic import BaseModel, Field


class TaskSchemas(BaseModel):
    """计划的模型类"""
    id: int = Field(description="任务id", )
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")
    name: str = Field(description="任务名称")
    task_type: int = Field(description="任务类型")
    project_id: int = Field(description="所属项目")
    username: str = Field(description="创建人")


class AddTaskForm(BaseModel):
    """创建计划的表单"""
    name: str = Field(description="任务名称")
    project_id: int = Field(description="所属项目")
    username: str = Field(description="创建人")
    task_type: int = Field(description="任务类型")


class UpdateTaskForm(BaseModel):
    """更新计划的表单"""
    name: str | None = Field(default=None, description="任务名称")
    task_type: int = Field(description="任务类型")


class AddSuiteToTaskForm(BaseModel):
    """创建计划的套件的表单"""
    suite_id: int = Field(description="套件id")
    task_type: int = Field(description="任务类型")


class TaskToSuiteSchemas(BaseModel):
    suite_id: int = Field(description="套件id")
    suite_name: str = Field(description="套件名称")
    suite_type: str = Field(description="套件类型")
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")


class TaskDetailSchemas(BaseModel):
    id: int = Field(description="任务id")
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")
    name: str = Field(description="任务名称")
    suites: list[TaskToSuiteSchemas] = Field(description="任务中套件")
    username: str = Field(description="创建人")
    task_type: int = Field(description="任务类型")
