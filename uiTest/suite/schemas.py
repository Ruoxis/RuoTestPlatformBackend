from datetime import datetime
from pydantic import BaseModel, Field


class SuiteSchemas(BaseModel):
    """测试套件返回数据类型"""
    id: int = Field(description="套件id")
    name: str = Field(description="套件名称")
    project_id: int = Field(description="所属项目id")
    modules_id: int = Field(description="所属模块id")
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")
    suite_setup_step: list = Field(description="前置执行步骤")
    suite_type: str = Field(description="套件类型")
    username: str = Field(description="创建人")


class AddSuiteForm(BaseModel):
    """创建测试套件的参数表单"""
    name: str = Field(description="套件名称")
    project_id: int = Field(description="所属项目id")
    modules_id: int = Field(description="所属模块id")
    suite_setup_step: list = Field(description="前置执行步骤")
    suite_type: str = Field(description="套件类型")
    username: str = Field(description="创建人")


class UpdateSuiteForm(BaseModel):
    """修改测试套件的参数表单"""
    name: str | None = Field(default=None, description="套件名称")
    modules_id: int | None = Field(default=None, description="所属模块id")
    suite_setup_step: list | None = Field(default=None, description="前置执行步骤")
    suite_type: str | None = Field(default=None, description="套件类型")


class StepSchemas(BaseModel):
    """套件中的用例模型类"""
    id: int = Field(description="用例id")
    suite_id: int = Field(description="所属套件")
    cases_id: int = Field(description="所属用例")
    sort: int = Field(description="用例执行顺序")
    skip: bool = Field(description="是否跳过")


class StepListSchemas(StepSchemas):
    """获取套件中的所以的用例模型类"""
    suite_name: str = Field(description="套件名称")
    cases_name: str = Field(description="用例名称")


class AddStepForm(BaseModel):
    """添加用例到套件中的表单"""
    cases_id: int = Field(description="所属用例")
    sort: int = Field(description="用例执行顺序")


class UpdateCaseSortForm(BaseModel):
    """修改用例顺序的表单"""
    id: int | None = Field(default=None, description="用例id")
    sort: int | None = Field(default=None, description="用例执行顺序")
