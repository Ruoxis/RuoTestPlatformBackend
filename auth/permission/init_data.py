"""
权限系统初始化脚本
用于创建默认的角色和权限数据
"""
import sys
from pathlib import Path
from tortoise import Tortoise

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.permission.models import Role, Permission, RolePermission
from common.settings import TORTOISE_ORM


async def init_tortoise():
    """初始化Tortoise ORM"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def init_roles_and_permissions():
    """初始化角色和权限数据"""
    
    # 创建默认角色
    default_roles = [
        {
            "name": "系统管理员",
            "description": "拥有系统所有权限的超级管理员",
            "level": 1,
            "is_system": True
        },
        {
            "name": "项目管理员",
            "description": "管理特定项目的管理员",
            "level": 2,
            "is_system": True
        },
        {
            "name": "项目成员",
            "description": "项目的普通成员",
            "level": 3,
            "is_system": True
        },
        {
            "name": "其他用户",
            "description": "只拥有公开项目只读权限的用户",
            "level": 4,
            "is_system": True
        }
    ]
    
    for role_data in default_roles:
        await Role.get_or_create(
            name=role_data["name"],
            defaults=role_data
        )
    
    # 创建常用权限
    common_permissions = [
        # 项目相关权限
        {"name": "项目查看", "code": "project:read", "description": "查看项目信息", "category": "project"},
        {"name": "项目创建", "code": "project:create", "description": "创建新项目", "category": "project"},
        {"name": "项目更新", "code": "project:update", "description": "更新项目信息", "category": "project"},
        {"name": "项目删除", "code": "project:delete", "description": "删除项目", "category": "project"},
        
        # 测试用例相关权限
        {"name": "用例查看", "code": "case:read", "description": "查看测试用例", "category": "case"},
        {"name": "用例创建", "code": "case:create", "description": "创建测试用例", "category": "case"},
        {"name": "用例更新", "code": "case:update", "description": "更新测试用例", "category": "case"},
        {"name": "用例删除", "code": "case:delete", "description": "删除测试用例", "category": "case"},
        
        # 测试套件相关权限
        {"name": "套件查看", "code": "suite:read", "description": "查看测试套件", "category": "suite"},
        {"name": "套件创建", "code": "suite:create", "description": "创建测试套件", "category": "suite"},
        {"name": "套件更新", "code": "suite:update", "description": "更新测试套件", "category": "suite"},
        {"name": "套件删除", "code": "suite:delete", "description": "删除测试套件", "category": "suite"},
        
        # 测试运行相关权限
        {"name": "运行测试", "code": "run:execute", "description": "执行测试", "category": "run"},
        {"name": "查看结果", "code": "run:read", "description": "查看测试结果", "category": "run"},
        
        # 环境相关权限
        {"name": "环境查看", "code": "env:read", "description": "查看测试环境", "category": "environment"},
        {"name": "环境创建", "code": "env:create", "description": "创建测试环境", "category": "environment"},
        {"name": "环境更新", "code": "env:update", "description": "更新测试环境", "category": "environment"},
        {"name": "环境删除", "code": "env:delete", "description": "删除测试环境", "category": "environment"},
        
        # 用户管理权限
        {"name": "用户查看", "code": "user:read", "description": "查看用户信息", "category": "user"},
        {"name": "用户管理", "code": "user:manage", "description": "管理用户权限", "category": "user"},
        
        # 系统管理权限
        {"name": "系统配置", "code": "system:config", "description": "系统配置管理", "category": "system"},
        {"name": "权限管理", "code": "permission:manage", "description": "权限管理", "category": "system"}
    ]
    
    for perm_data in common_permissions:
        await Permission.get_or_create(
            code=perm_data["code"],
            defaults=perm_data
        )
    
    # 为默认角色分配权限
    await assign_default_role_permissions()


async def assign_default_role_permissions():
    """为默认角色分配权限"""
    
    # 获取所有角色和权限
    roles = await Role.all()
    permissions = await Permission.all()
    
    # 创建权限映射
    permission_map = {p.code: p for p in permissions}
    role_map = {r.name: r for r in roles}
    
    # 系统管理员拥有所有权限
    system_admin = role_map.get("系统管理员")
    if system_admin:
        for permission in permissions:
            await RolePermission.get_or_create(
                role=system_admin,
                permission=permission
            )
    
    # 项目管理员权限
    project_admin = role_map.get("项目管理员")
    if project_admin:
        project_admin_permissions = [
            "project:read", "project:update", "project:delete",
            "case:read", "case:create", "case:update", "case:delete",
            "suite:read", "suite:create", "suite:update", "suite:delete",
            "run:execute", "run:read",
            "env:read", "env:create", "env:update", "env:delete",
            "user:read"
        ]
        for perm_code in project_admin_permissions:
            permission = permission_map.get(perm_code)
            if permission:
                await RolePermission.get_or_create(
                    role=project_admin,
                    permission=permission
                )
    
    # 项目成员权限
    project_member = role_map.get("项目成员")
    if project_member:
        project_member_permissions = [
            "project:read",
            "case:read", "case:create", "case:update",
            "suite:read", "suite:create",
            "run:execute", "run:read",
            "env:read"
        ]
        for perm_code in project_member_permissions:
            permission = permission_map.get(perm_code)
            if permission:
                await RolePermission.get_or_create(
                    role=project_member,
                    permission=permission
                )
    
    # 其他用户权限（只读权限）
    other_user = role_map.get("其他用户")
    if other_user:
        other_user_permissions = [
            "project:read",
            "case:read",
            "suite:read",
            "run:read",
            "env:read"
        ]
        for perm_code in other_user_permissions:
            permission = permission_map.get(perm_code)
            if permission:
                await RolePermission.get_or_create(
                    role=other_user,
                    permission=permission
                )


async def init_permission_system():
    """初始化整个权限系统"""
    await init_tortoise()
    await init_roles_and_permissions()
    print("权限系统初始化完成")
    await Tortoise.close_connections()


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_permission_system())