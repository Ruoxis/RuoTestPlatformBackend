from pydantic import BaseModel, Field


class Cronjob(BaseModel):
    """定时任务模型类"""
    minute: str = Field(default="30", description="分钟")
    hour: str = Field(default="*", description="小时")
    day: str = Field(default="*", description="天")
    month: str = Field(default="*", description="月")
    day_of_week: str = Field(default="*", description="星期")


class CronjobForm(BaseModel):
    """定时任务表单"""
    name: str = Field(max_length=50, description="任务名称")
    project: int = Field(description="所属项目")
    env: int = Field(description="执行环境")
    task: int = Field(description="执行的测试计划")
    state: bool = Field(default=False, description="是否启用")
    run_type: str = Field(max_length=10, description="任务类型", default="Interval")
    interval: int = Field(default=60, description="执行间隔时间")
    cronjob_type: int | None = Field(default=0, description="任务类型")
    date: str = Field(default="2030-01-01 00:00:00", description="指定执行的事件")
    crontab: Cronjob = Field(default=Cronjob(minute="30", hour="*", day="*", month="*", day_of_week="*"),
                             description="周期性任务规则")
    username: str = Field(max_length=50, description="创建人")


class CronjobUpdateForm(BaseModel):
    """定时任务更新表单"""
    name: str | None = Field(default=None, max_length=50, description="任务名称")
    state: bool | None = Field(default=False, description="是否启用")
    run_type: str | None = Field(max_length=10, description="任务类型", default="Interval")
    interval: int | None = Field(default=60, description="执行间隔时间")
    cronjob_type: int | None = Field(default=0, description="任务类型")
    date: str | None = Field(default="2030-01-01 00:00:00", description="指定执行的事件")
    crontab: Cronjob | None = Field(default=Cronjob(minute="30", hour="*", day="*", month="*", day_of_week="*"),
                                    description="周期性任务规则")
