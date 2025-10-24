from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class RunForm(BaseModel):
    """用例运行表单"""
    env_id: int = Field(description="运行环境的ID")
    browser_type: str | None = Field(default=None, description="浏览器类型")
    device_id: str | None = Field(default=None, description="设备ID")
    device_ids: List[str] | None = Field(default=None, description="设备ID列表")
    config: bool | None = Field(default=True, description="是否启用无头模式")
    username: str = Field(description="创建人")
    reset_cache: bool | None = Field(default=False, description="是否重置缓存")


class SuiteResultSchemas(BaseModel):
    """套件结果模型类"""
    id: int = Field(description="套件记录id")
    status: str = Field(description="运行状态")
    suite_id: int = Field(description="套件id")
    suite_name: str = Field(description="套件名称")
    username: str = Field(description="创建人")
    start_time: datetime = Field(description="开始时间")
    success: int = Field(description="成功用例数")
    error: int = Field(description="错误用例数")
    skip: int = Field(description="跳过用例数")
    duration: float = Field(description="执行时间")
    pass_rate: float = Field(description="通过率")
    run_all: int = Field(description="执行用例数")
    all: int = Field(description="总用例数")
    fail: int = Field(description="失败用例数")
    suite_log: list = Field(description="套件执行日志")
    no_run: int = Field(description="未执行用例数")
    env: dict = Field(description="运行环境", default_factory=dict)


class TaskResultSchemas(BaseModel):
    """计划结果模型类"""
    id: int = Field(description="任务记录id")
    project_id: int = Field(description="所属项目id")
    start_time: datetime = Field(description="开始时间")
    task_id: int = Field(description="任务id")
    task_name: str = Field(description="任务名称")
    username: str = Field(description="创建人")
    duration: float = Field(description="执行时间")
    pass_rate: float = Field(description="通过率")
    no_run: int = Field(description="未执行用例数")
    success: int = Field(description="成功用例数")
    error: int = Field(description="错误用例数")
    skip: int = Field(description="跳过用例数")
    all: int = Field(description="总用例数")
    fail: int = Field(description="失败用例数")
    run_all: int = Field(description="执行用例数")
    status: str = Field(description="运行状态")
    env: dict = Field(description="运行环境", default_factory=dict)
