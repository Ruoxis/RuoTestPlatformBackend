"""
权限工具类
提供权限检查的统一接口，用于在业务逻辑中调用
"""
from typing import Optional, List
from .models import Role, Permission, ProjectRole, RolePermission
from auth.user.models import User


class PermissionService:
    """权限服务类"""
    
    @staticmethod
    async def has_permission(
        user_id: int,
        permission_code: str,
        project_id: Optional[int] = None
    ) -> bool:
        """
        检查用户是否有指定权限
        
        Args:
            user_id: 用户ID
            permission_code: 权限代码
            project_id: 项目ID（可选）
        
        Returns:
            bool: 是否有权限
        """
        
        # 超级管理员拥有所有权限
        user = await User.get_or_none(id=user_id)
        if user and user.is_superuser:
            return True
        
        # 如果没有指定项目，检查系统级权限
        if project_id is None:
            # 检查是否为系统管理员
            system_admin_role = await Role.get_or_none(level=1)
            if system_admin_role:
                has_system_role = await ProjectRole.filter(
                    user_id=user_id,
                    role_id=system_admin_role.id
                ).exists()
                if has_system_role:
                    # 检查系统管理员角色是否有该权限
                    has_permission = await RolePermission.filter(
                        role_id=system_admin_role.id,
                        permission__code=permission_code
                    ).exists()
                    if has_permission:
                        return True
            
            # 系统级权限不能通过项目角色获得
            return False
        
        # 检查项目级权限
        if project_id:
            project_role = await ProjectRole.filter(
                user_id=user_id,
                project_id=project_id
            ).prefetch_related("role").first()
            
            if project_role:
                # 检查角色是否有该权限
                has_permission = await RolePermission.filter(
                    role_id=project_role.role.id,
                    permission__code=permission_code
                ).exists()
                
                return has_permission
        
        return False
    
    @staticmethod
    async def get_user_permissions(
        user_id: int,
        project_id: Optional[int] = None
    ) -> List[str]:
        """
        获取用户的权限列表
        
        Args:
            user_id: 用户ID
            project_id: 项目ID（可选）
        
        Returns:
            List[str]: 权限代码列表
        """
        
        # 超级管理员拥有所有权限
        user = await User.get_or_none(id=user_id)
        if user and user.is_superuser:
            permissions = await Permission.filter(is_active=True).values_list("code", flat=True)
            return list(permissions)
        
        # 如果没有指定项目，检查系统级权限
        if project_id is None:
            # 检查是否为系统管理员
            system_admin_role = await Role.get_or_none(level=1)
            if system_admin_role:
                has_system_role = await ProjectRole.filter(
                    user_id=user_id,
                    role_id=system_admin_role.id
                ).exists()
                if has_system_role:
                    permissions = await Permission.filter(is_active=True).values_list("code", flat=True)
                    return list(permissions)
        
        # 检查项目级权限
        if project_id:
            project_role = await ProjectRole.filter(
                user_id=user_id,
                project_id=project_id
            ).prefetch_related("role").first()
            
            if project_role:
                permissions = await Permission.filter(
                    roles__role_id=project_role.role.id,
                    is_active=True
                ).values_list("code", flat=True)
                
                return list(permissions)
        
        return []
    
    @staticmethod
    async def get_user_projects_with_permissions(user_id: int) -> List[dict]:
        """
        获取用户有权限的所有项目
        
        Args:
            user_id: 用户ID
        
        Returns:
            List[dict]: 项目信息列表
        """
        
        # 超级管理员返回所有项目
        user = await User.get_or_none(id=user_id)
        if user and user.is_superuser:
            from wealth.project.models import Project
            projects = await Project.all().values("id", "name", "create_time")
            return [{
                "project_id": p["id"],
                "project_name": p["name"],
                "role_name": "系统管理员",
                "role_level": 1,
                "permissions": await PermissionService.get_user_permissions(user_id)
            } for p in projects]
        
        # 获取用户的项目角色信息
        project_roles = await ProjectRole.filter(
            user_id=user_id
        ).prefetch_related("project", "role")
        
        result = []
        for pr in project_roles:
            permissions = await Permission.filter(
                roles__role_id=pr.role.id,
                is_active=True
            ).values_list("code", flat=True)
            
            result.append({
                "project_id": pr.project.id,
                "project_name": pr.project.name,
                "role_name": pr.role.name,
                "role_level": pr.role.level,
                "permissions": list(permissions)
            })
        
        return result
    
    @staticmethod
    async def get_project_users_with_roles(project_id: int) -> List[dict]:
        """
        获取项目的用户及其角色信息
        
        Args:
            project_id: 项目ID
        
        Returns:
            List[dict]: 用户信息列表
        """
        
        project_roles = await ProjectRole.filter(
            project_id=project_id
        ).prefetch_related("user", "role")
        
        result = []
        for pr in project_roles:
            permissions = await Permission.filter(
                roles__role_id=pr.role.id,
                is_active=True
            ).values_list("code", flat=True)
            
            result.append({
                "user_id": pr.user.id,
                "username": pr.user.username,
                "nickname": pr.user.nickname,
                "role_id": pr.role.id,
                "role_name": pr.role.name,
                "role_level": pr.role.level,
                "permissions": list(permissions),
                "granted_by": pr.granted_by,
                "created_at": pr.created_at
            })
        
        return result
    
    @staticmethod
    async def get_role_permissions(role_id: int) -> List[str]:
        """
        获取角色的权限列表
        
        Args:
            role_id: 角色ID
        
        Returns:
            List[str]: 权限代码列表
        """
        
        permissions = await Permission.filter(
            roles__role_id=role_id,
            is_active=True
        ).values_list("code", flat=True)
        
        return list(permissions)
    
    @staticmethod
    async def assign_role_to_user(
        user_id: int,
        project_id: int,
        role_id: int,
        granted_by: int
    ) -> bool:
        """
        为用户分配角色
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            role_id: 角色ID
            granted_by: 授权人ID
        
        Returns:
            bool: 是否成功
        """
        
        from wealth.project.models import Project
        
        # 检查用户、项目、角色是否存在
        user = await User.get_or_none(id=user_id)
        project = await Project.get_or_none(id=project_id)
        role = await Role.get_or_none(id=role_id)
        
        if not all([user, project, role]):
            return False
        
        # 创建或更新项目角色
        await ProjectRole.update_or_create(
            user_id=user_id,
            project_id=project_id,
            defaults={
                'role_id': role_id,
                'granted_by': granted_by
            }
        )
        
        return True
    
    @staticmethod
    async def remove_user_from_project(user_id: int, project_id: int) -> bool:
        """
        将用户从项目中移除
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
        
        Returns:
            bool: 是否成功
        """
        
        project_role = await ProjectRole.filter(
            user_id=user_id,
            project_id=project_id
        ).first()
        
        if project_role:
            await project_role.delete()
            return True
        
        return False


# 创建单例实例
permission_service = PermissionService()