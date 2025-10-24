from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class RoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(description="角色名称", max_length=50)
    description: str = Field(description="角色描述", max_length=255, default="")
    level: int = Field(description="角色等级 1:系统管理员 2:项目管理员 3:项目成员 4:其他用户 5:自定义角色")
    is_active: bool = Field(description="是否启用", default=True)


class RoleCreate(RoleBase):
    """创建角色"""
    pass


class RoleUpdate(BaseModel):
    """更新角色"""
    name: Optional[str] = Field(description="角色名称", max_length=50, default=None)
    description: Optional[str] = Field(description="角色描述", max_length=255, default=None)
    is_active: Optional[bool] = Field(description="是否启用", default=None)


class RoleSchema(RoleBase):
    """角色详情"""
    id: int = Field(description="角色id")
    is_system: bool = Field(description="是否为系统内置角色")
    created_at: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class RoleList(BaseModel):
    """角色列表"""
    total: int = Field(description="总数")
    data: List[RoleSchema] = Field(description="数据")


class PermissionBase(BaseModel):
    """权限基础模型"""
    name: str = Field(description="权限名称", max_length=50)
    code: str = Field(description="权限代码", max_length=100)
    description: str = Field(description="权限描述", max_length=255, default="")
    category: str = Field(description="权限分类", max_length=50, default="")
    is_active: bool = Field(description="是否启用", default=True)


class PermissionCreate(PermissionBase):
    """创建权限"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限"""
    name: Optional[str] = Field(description="权限名称", max_length=50, default=None)
    description: Optional[str] = Field(description="权限描述", max_length=255, default=None)
    category: Optional[str] = Field(description="权限分类", max_length=50, default=None)
    is_active: Optional[bool] = Field(description="是否启用", default=None)


class PermissionSchema(PermissionBase):
    """权限详情"""
    id: int = Field(description="权限id")
    created_at: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class PermissionList(BaseModel):
    """权限列表"""
    total: int = Field(description="总数")
    data: List[PermissionSchema] = Field(description="数据")


class ProjectRoleBase(BaseModel):
    """项目角色基础模型"""
    user_id: int = Field(description="用户id")
    project_id: int = Field(description="项目id")
    role_id: int = Field(description="角色id")


class ProjectRoleCreate(ProjectRoleBase):
    """创建项目角色"""
    pass


class ProjectRoleUpdate(BaseModel):
    """更新项目角色"""
    role_id: int = Field(description="角色id")


class ProjectRoleSchema(BaseModel):
    """项目角色详情"""
    id: int = Field(description="id")
    user_id: int = Field(description="用户id")
    project_id: int = Field(description="项目id")
    role_id: int = Field(description="角色id")
    role_name: str = Field(description="角色名称")
    role_level: int = Field(description="角色等级")
    granted_by: Optional[int] = Field(description="授权人id")
    created_at: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True


class ProjectRoleList(BaseModel):
    """项目角色列表"""
    total: int = Field(description="总数")
    data: List[ProjectRoleSchema] = Field(description="数据")


class UserProjectRole(BaseModel):
    """用户项目角色信息"""
    project_id: int = Field(description="项目id")
    project_name: str = Field(description="项目名称")
    role_id: int = Field(description="角色id")
    role_name: str = Field(description="角色名称")
    role_level: int = Field(description="角色等级")
    permissions: List[str] = Field(description="权限代码列表")


class UserPermissionCheck(BaseModel):
    """权限检查请求"""
    project_id: Optional[int] = Field(description="项目id", default=None)
    permission_code: str = Field(description="权限代码")


class BatchGrantRole(BaseModel):
    """批量授权"""
    user_ids: List[int] = Field(description="用户id列表")
    project_id: int = Field(description="项目id")
    role_id: int = Field(description="角色id")