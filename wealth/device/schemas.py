from pydantic import BaseModel, Field


class DeviceSchemas(BaseModel):
    """设备列表模型类"""
    id: str = Field(description="设备id")
    ip: str = Field(description="设备ip")
    name: str = Field(description="设备名称")
    system: str = Field(description="操作系统")
    status: str = Field(description="设备状态")
    username: str = Field(description="创建人")
    version: str = Field(description="设备版本")
    hostname: str = Field(description="设备主机名")
