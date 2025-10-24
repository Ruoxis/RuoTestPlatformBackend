"""
权限系统数据库迁移脚本
用于在现有项目中部署权限系统
"""
import asyncio
import logging
from tortoise import Tortoise
from common.settings import TORTOISE_ORM
from auth.permission.init_data import init_permission_system


async def migrate_permission_system():
    """执行权限系统迁移"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化数据库连接
        await Tortoise.init(config=TORTOISE_ORM)
        
        logger.info("开始权限系统迁移...")
        
        # 生成权限系统的表结构
        await Tortoise.generate_schemas()
        logger.info("权限系统表结构创建完成")
        
        # 初始化权限数据
        await init_permission_system()
        logger.info("权限数据初始化完成")
        
        # 为现有用户创建默认权限
        await migrate_existing_users()
        logger.info("现有用户权限迁移完成")
        
        logger.info("权限系统迁移完成！")
        
    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        raise
    finally:
        await Tortoise.close_connections()


async def migrate_existing_users():
    """为现有用户创建默认权限"""
    from auth.user.models import User
    from wealth.project.models import Project
    from auth.permission.models import Role, ProjectRole
    
    # 获取"其他用户"角色
    other_user_role = await Role.get_or_none(name="其他用户")
    if not other_user_role:
        print("警告：未找到'其他用户'角色，跳过现有用户权限迁移")
        return
    
    # 获取所有用户和项目
    users = await User.all()
    projects = await Project.all()
    
    if not users or not projects:
        print("没有用户或项目，跳过权限迁移")
        return
    
    # 为每个用户在所有项目中创建"其他用户"角色
    # 注意：这里只给超级管理员创建项目管理员角色，其他用户不自动分配
    # 这样可以避免给所有用户不必要的权限
    
    # 获取系统管理员角色
    system_admin_role = await Role.get_or_none(name="系统管理员")
    project_admin_role = await Role.get_or_none(name="项目管理员")
    
    for project in projects:
        # 为项目创建者分配项目管理员角色
        if project_admin_role:
            await ProjectRole.update_or_create(
                user_id=project.user_id,
                project_id=project.id,
                defaults={
                    'role_id': project_admin_role.id,
                    'granted_by': project.user_id
                }
            )
        
        # 为超级管理员分配系统管理员角色
        if system_admin_role:
            super_admins = await User.filter(is_superuser=True)
            for admin in super_admins:
                await ProjectRole.update_or_create(
                    user_id=admin.id,
                    project_id=project.id,
                    defaults={
                        'role_id': system_admin_role.id,
                        'granted_by': admin.id
                    }
                )


async def check_migration_status():
    """检查权限系统迁移状态"""
    from auth.permission.models import Role, Permission, ProjectRole

    try:
        await Tortoise.init(config=TORTOISE_ORM)
        
        # 检查表是否存在
        tables = ["role", "permission", "project_role", "role_permission"]
        for table in tables:
            try:
                count = await Role.raw(f"SELECT COUNT(*) FROM {table}").first()
                print(f"表 {table} 已存在，记录数: {count}")
            except Exception as e:
                print(f"表 {table} 不存在或查询失败: {e}")
        
        # 检查默认数据
        roles = await Role.all()
        permissions = await Permission.all()
        project_roles = await ProjectRole.all()
        
        print(f"角色数量: {len(roles)}")
        print(f"权限数量: {len(permissions)}")
        print(f"项目角色关联数量: {len(project_roles)}")
        
        # 打印默认角色
        print("\n默认角色:")
        for role in roles:
            print(f"  - {role.name} (等级: {role.level})")
        
        # 打印权限分类
        print("\n权限分类:")
        categories = set()
        for perm in permissions:
            categories.add(perm.category)
        
        for category in sorted(categories):
            category_perms = await Permission.filter(category=category)
            print(f"  {category}: {len(category_perms)} 个权限")
            
    except Exception as e:
        print(f"检查迁移状态失败: {e}")
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "migrate":
            asyncio.run(migrate_permission_system())
        elif sys.argv[1] == "check":
            asyncio.run(check_migration_status())
        else:
            print("用法: python migration.py [migrate|check]")
    else:
        asyncio.run(migrate_permission_system())