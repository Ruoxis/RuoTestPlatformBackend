"""
权限装饰器
用于在现有接口上添加权限控制，实现最小改动原则
"""
from functools import wraps
from fastapi import HTTPException, status, Depends
from typing import Optional
from .models import Role, ProjectRole, RolePermission
from auth.user.models import User
from auth.auth import is_authenticated


async def check_user_permission(
    user_id: int,
    permission_code: str,
    project_id: Optional[int] = None
) -> bool:
    """
    检查用户权限
    
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
    
    # 如果没有指定项目（系统级权限），检查用户权限
    if project_id is None:
        # 超级管理员拥有所有权限
        user = await User.get_or_none(id=user_id)
        if user and user.is_superuser:
            return True
            
        # 检查用户是否有系统级角色（系统管理员）
        # 系统级权限只能由系统管理员角色授予，不能通过项目角色获得
        system_admin_role = await Role.get_or_none(level=1)  # 系统管理员
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
        
        # 注意：项目角色不应该影响系统级权限的判断
        # 即使用户在某个项目中是项目管理员，也不应该拥有系统级权限
    
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


def require_permission(permission_code: str, project_id_param: Optional[str] = None):
    """
    权限检查装饰器
    
    Args:
        permission_code: 权限代码
        project_id_param: 项目ID参数名（从路径参数或查询参数中获取）
    
    使用示例:
        @router.get("/project/{project_id}/cases")
        @require_permission("case:read", "project_id")
        async def get_cases(project_id: int, user_info: dict = Depends(is_authenticated)):
            ...
    """
    def decorator(func):
        # 获取函数签名
        import inspect
        sig = inspect.signature(func)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取用户信息 - 优先从函数参数中获取
            user_info = None
            
            # 方法1: 从kwargs中查找
            if 'user_info' in kwargs:
                user_info = kwargs['user_info']
            elif 'current_user' in kwargs:
                user_info = kwargs['current_user']
            else:
                # 方法2: 检查函数参数中是否有user_info
                for param_name, param_value in kwargs.items():
                    if isinstance(param_value, dict) and 'id' in param_value and 'username' in param_value:
                        user_info = param_value
                        break
                
                # 方法3: 从args中查找（如果函数定义了user_info参数）
                if not user_info and args:
                    # 获取函数参数名
                    func_params = list(sig.parameters.keys())
                    for i, (param_name, param_value) in enumerate(zip(func_params, args)):
                        if param_name in ['user_info', 'current_user'] and isinstance(param_value, dict):
                            user_info = param_value
                            break
            
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户未登录或无法获取用户信息"
                )
            
            user_id = user_info.get('id')
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的用户信息"
                )
            
            # 获取项目ID
            project_id = None
            if project_id_param:
                if project_id_param in kwargs:
                    project_id = kwargs[project_id_param]
                else:
                    # 从路径参数、查询参数、请求体中获取项目ID
                    project_id = kwargs.get('project_id')
                    if not project_id:
                        project_id = kwargs.get('id')
            
            # 检查权限
            has_permission = await check_user_permission(
                user_id=user_id,
                permission_code=permission_code,
                project_id=project_id
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"没有{permission_code}权限，请联系管理员"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PermissionChecker:
    """权限检查类，用于在路由中使用"""
    
    def __init__(self, permission_code: str, project_id_param: Optional[str] = None):
        self.permission_code = permission_code
        self.project_id_param = project_id_param
    
    async def __call__(self, user_info: dict = Depends(is_authenticated)):
        user_id = user_info.get('id')
        
        # 超级管理员拥有所有权限
        user = await User.get_or_none(id=user_id)
        if user and user.is_superuser:
            return user_info
        
        # 如果没有指定项目，检查系统级权限
        if not self.project_id_param:
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
                        permission__code=self.permission_code
                    ).exists()
                    if has_permission:
                        return user_info
            
            # 系统级权限不能通过项目角色获得
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"没有权限: {self.permission_code}"
            )
        
        # 对于项目级权限，这里只是返回用户信息，具体检查在路由中进行
        return user_info


def get_project_id_from_request(kwargs):
    """从请求参数中获取项目ID"""
    # 从路径参数、查询参数、请求体中获取项目ID
    project_id = kwargs.get('project_id')
    if not project_id:
        project_id = kwargs.get('id')  # 有些路由使用id作为项目ID
    return project_id


# 预定义的权限代码
class Permissions:
    """预定义的权限代码"""
    
    # 项目相关权限
    PROJECT_READ = "project:read"
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    
    # 测试用例相关权限
    CASE_READ = "case:read"
    CASE_CREATE = "case:create"
    CASE_UPDATE = "case:update"
    CASE_DELETE = "case:delete"
    
    # 测试套件相关权限
    SUITE_READ = "suite:read"
    SUITE_CREATE = "suite:create"
    SUITE_UPDATE = "suite:update"
    SUITE_DELETE = "suite:delete"
    
    # 测试运行相关权限
    RUN_EXECUTE = "run:execute"
    RUN_READ = "run:read"
    
    # 环境相关权限
    ENV_READ = "env:read"
    ENV_CREATE = "env:create"
    ENV_UPDATE = "env:update"
    ENV_DELETE = "env:delete"
    
    # 用户管理权限
    USER_READ = "user:read"
    USER_MANAGE = "user:manage"
    
    # 系统管理权限
    SYSTEM_CONFIG = "system:config"
    PERMISSION_MANAGE = "permission:manage"