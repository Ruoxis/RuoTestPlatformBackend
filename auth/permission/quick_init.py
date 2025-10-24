"""
权限系统快速初始化工具
解决数据库连接初始化问题
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from common.settings import TORTOISE_ORM
from auth.permission.models import Role, Permission, RolePermission


async def init_database():
    """初始化数据库连接"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def init_roles():
    """初始化默认角色"""
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
        role, created = await Role.get_or_create(
            name=role_data["name"],
            defaults=role_data
        )
        print(f"{'创建' if created else '已存在'}角色: {role.name}")


async def init_permissions():
    """初始化权限"""
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
        permission, created = await Permission.get_or_create(
            code=perm_data["code"],
            defaults=perm_data
        )
        print(f"{'创建' if created else '已存在'}权限: {permission.code}")


async def assign_role_permissions():
    """为角色分配权限"""
    # 获取所有角色和权限
    roles = {r.name: r for r in await Role.all()}
    permissions = {p.code: p for p in await Permission.all()}
    
    # 系统管理员拥有所有权限
    if "系统管理员" in roles:
        system_admin = roles["系统管理员"]
        for permission in permissions.values():
            await RolePermission.get_or_create(
                role=system_admin,
                permission=permission
            )
        print("为系统管理员分配了所有权限")
    
    # 项目管理员权限
    if "项目管理员" in roles:
        project_admin = roles["项目管理员"]
        project_admin_permissions = [
            "project:read", "project:update", "project:delete",
            "case:read", "case:create", "case:update", "case:delete",
            "suite:read", "suite:create", "suite:update", "suite:delete",
            "run:execute", "run:read",
            "env:read", "env:create", "env:update", "env:delete",
            "user:read"
        ]
        for perm_code in project_admin_permissions:
            if perm_code in permissions:
                await RolePermission.get_or_create(
                    role=project_admin,
                    permission=permissions[perm_code]
                )
        print("为项目管理员分配了权限")
    
    # 项目成员权限
    if "项目成员" in roles:
        project_member = roles["项目成员"]
        project_member_permissions = [
            "project:read",
            "case:read", "case:create", "case:update",
            "suite:read", "suite:create",
            "run:execute", "run:read",
            "env:read"
        ]
        for perm_code in project_member_permissions:
            if perm_code in permissions:
                await RolePermission.get_or_create(
                    role=project_member,
                    permission=permissions[perm_code]
                )
        print("为项目成员分配了权限")
    
    # 其他用户权限（只读权限）
    if "其他用户" in roles:
        other_user = roles["其他用户"]
        other_user_permissions = [
            "project:read",
            "case:read",
            "suite:read",
            "run:read",
            "env:read"
        ]
        for perm_code in other_user_permissions:
            if perm_code in permissions:
                await RolePermission.get_or_create(
                    role=other_user,
                    permission=permissions[perm_code]
                )
        print("为其他用户分配了权限")


async def main():
    """主函数"""
    print("🚀 开始初始化权限系统...")
    
    try:
        print("📊 初始化数据库连接...")
        await init_database()
        
        print("👥 创建默认角色...")
        await init_roles()
        
        print("🔐 创建权限...")
        await init_permissions()
        
        print("🔗 分配角色权限...")
        await assign_role_permissions()
        
        print("✅ 权限系统初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())