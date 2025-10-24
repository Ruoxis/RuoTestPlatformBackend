from fastapi import APIRouter, HTTPException, status, Depends
from .models import Role, Permission, ProjectRole, RolePermission
from .schemas import *
from auth.user.models import User
from wealth.project.models import Project
from auth.auth import is_authenticated

router = APIRouter(prefix="/permission", tags=["权限管理"])


@router.post("/role", summary="创建角色", response_model=RoleSchema)
async def create_role(role: RoleCreate, user_info: dict = Depends(is_authenticated)):
    """创建角色"""
    # 检查角色名称是否已存在
    existing_role = await Role.get_or_none(name=role.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名称已存在"
        )
    
    new_role = await Role.create(**role.dict())
    return RoleSchema.model_validate(new_role)


@router.get("/role", summary="获取角色列表", response_model=RoleList)
async def get_roles(
    page: int = 1,
    size: int = 10,
    user_info: dict = Depends(is_authenticated)
):
    """获取角色列表"""
    query = Role.all().order_by("-id")
    total = await query.count()
    roles = await query.offset((page - 1) * size).limit(size)
    
    return RoleList(
        total=total,
        data=[RoleSchema.model_validate(role) for role in roles]
    )


@router.get("/role/{role_id}", summary="获取角色详情", response_model=RoleSchema)
async def get_role_detail(role_id: int, user_info: dict = Depends(is_authenticated)):
    """获取角色详情"""
    role = await Role.get_or_none(id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return RoleSchema.model_validate(role)


@router.put("/role/{role_id}", summary="更新角色", response_model=RoleSchema)
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    user_info: dict = Depends(is_authenticated)
):
    """更新角色"""
    role = await Role.get_or_none(id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 系统内置角色不允许修改名称
    if role.is_system and role_update.name is not None and role_update.name != role.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统内置角色名称不允许修改"
        )
    
    update_data = role_update.dict(exclude_unset=True)
    await role.update_from_dict(update_data)
    await role.save()
    
    return RoleSchema.model_validate(role)


@router.delete("/role/{role_id}", summary="删除角色")
async def delete_role(role_id: int, user_info: dict = Depends(is_authenticated)):
    """删除角色"""
    role = await Role.get_or_none(id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统内置角色不允许删除"
        )
    
    # 检查是否有用户在使用该角色
    role_count = await ProjectRole.filter(role_id=role_id).count()
    if role_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该角色正在被使用，无法删除"
        )
    
    await role.delete()
    return {"message": "删除成功"}


@router.post("/permission", summary="创建权限", response_model=PermissionSchema)
async def create_permission(
    permission: PermissionCreate,
    user_info: dict = Depends(is_authenticated)
):
    """创建权限"""
    # 检查权限代码是否已存在
    existing_permission = await Permission.get_or_none(code=permission.code)
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限代码已存在"
        )
    
    new_permission = await Permission.create(**permission.dict())
    return PermissionSchema.model_validate(new_permission)


@router.get("/permission", summary="获取权限列表", response_model=PermissionList)
async def get_permissions(
    page: int = 1,
    size: int = 10,
    category: str = None,
    user_info: dict = Depends(is_authenticated)
):
    """获取权限列表"""
    query = Permission.all().order_by("-id")
    if category:
        query = query.filter(category=category)
    
    total = await query.count()
    permissions = await query.offset((page - 1) * size).limit(size)
    
    return PermissionList(
        total=total,
        data=[PermissionSchema.model_validate(permission) for permission in permissions]
    )


@router.put("/permission/{permission_id}", summary="更新权限", response_model=PermissionSchema)
async def update_permission(
    permission_id: int,
    permission_update: PermissionUpdate,
    user_info: dict = Depends(is_authenticated)
):
    """更新权限"""
    permission = await Permission.get_or_none(id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    update_data = permission_update.dict(exclude_unset=True)
    await permission.update_from_dict(update_data)
    await permission.save()
    
    return PermissionSchema.model_validate(permission)


@router.delete("/permission/{permission_id}", summary="删除权限")
async def delete_permission(permission_id: int, user_info: dict = Depends(is_authenticated)):
    """删除权限"""
    permission = await Permission.get_or_none(id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    # 检查是否有角色在使用该权限
    usage_count = await RolePermission.filter(permission_id=permission_id).count()
    if usage_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该权限正在被使用，无法删除"
        )
    
    await permission.delete()
    return {"message": "删除成功"}


@router.post("/role/{role_id}/permissions", summary="为角色分配权限")
async def assign_permissions_to_role(
    role_id: int,
    permission_ids: List[int],
    user_info: dict = Depends(is_authenticated)
):
    """为角色分配权限"""
    role = await Role.get_or_none(id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查权限是否存在
    permissions = await Permission.filter(id__in=permission_ids)
    if len(permissions) != len(permission_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部分权限不存在"
        )
    
    # 删除现有权限关联
    await RolePermission.filter(role_id=role_id).delete()
    
    # 创建新的权限关联
    for permission in permissions:
        await RolePermission.create(role_id=role_id, permission_id=permission.id)
    
    return {"message": "权限分配成功"}


@router.get("/role/{role_id}/permissions", summary="获取角色的权限列表")
async def get_role_permissions(
    role_id: int,
    user_info: dict = Depends(is_authenticated)
):
    """获取角色的权限列表"""
    role = await Role.get_or_none(id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    permissions = await Permission.filter(
        roles__role_id=role_id
    ).order_by("-id")
    
    return [PermissionSchema.model_validate(permission) for permission in permissions]


@router.post("/project-role", summary="分配项目角色", response_model=ProjectRoleSchema)
async def assign_project_role(
    project_role: ProjectRoleCreate,
    user_info: dict = Depends(is_authenticated)
):
    """分配项目角色"""
    # 检查用户是否存在
    user = await User.get_or_none(id=project_role.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查项目是否存在
    project = await Project.get_or_none(id=project_role.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查角色是否存在
    role = await Role.get_or_none(id=project_role.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 创建或更新项目角色
    project_role_obj, created = await ProjectRole.update_or_create(
        user_id=project_role.user_id,
        project_id=project_role.project_id,
        defaults={
            'role_id': project_role.role_id,
            'granted_by': user_info.get('id')
        }
    )
    
    return ProjectRoleSchema.model_validate(project_role_obj)


@router.get("/project-role", summary="获取项目角色列表", response_model=ProjectRoleList)
async def get_project_roles(
    project_id: int,
    page: int = 1,
    size: int = 10,
    user_info: dict = Depends(is_authenticated)
):
    """获取项目角色列表"""
    query = ProjectRole.filter(project_id=project_id).prefetch_related("user", "role")
    total = await query.count()
    project_roles = await query.offset((page - 1) * size).limit(size)
    
    data = []
    for pr in project_roles:
        data.append(ProjectRoleSchema(
            id=pr.id,
            user_id=pr.user.id,
            project_id=pr.project.id,
            role_id=pr.role.id,
            role_name=pr.role.name,
            role_level=pr.role.level,
            granted_by=pr.granted_by,
            created_at=pr.created_at,
            update_time=pr.update_time
        ))
    
    return ProjectRoleList(total=total, data=data)


@router.post("/project-role/batch", summary="批量分配项目角色")
async def batch_assign_project_role(
    batch_grant: BatchGrantRole,
    user_info: dict = Depends(is_authenticated)
):
    """批量分配项目角色"""
    # 检查项目是否存在
    project = await Project.get_or_none(id=batch_grant.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查角色是否存在
    role = await Role.get_or_none(id=batch_grant.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查用户是否存在
    users = await User.filter(id__in=batch_grant.user_ids)
    if len(users) != len(batch_grant.user_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部分用户不存在"
        )
    
    # 批量创建或更新项目角色
    for user in users:
        await ProjectRole.update_or_create(
            user=user,
            project_id=batch_grant.project_id,
            defaults={
                'role_id': batch_grant.role_id,
                'granted_by': user_info.get('id')
            }
        )
    
    return {"message": "批量授权成功"}


@router.delete("/project-role/{project_role_id}", summary="删除项目角色")
async def delete_project_role(
    project_role_id: int,
    user_info: dict = Depends(is_authenticated)
):
    """删除项目角色"""
    project_role = await ProjectRole.get_or_none(id=project_role_id)
    if not project_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目角色不存在"
        )
    
    await project_role.delete()
    return {"message": "删除成功"}


@router.get("/user/{user_id}/projects", summary="获取用户的项目权限列表")
async def get_user_project_permissions(
    user_id: int,
    user_info: dict = Depends(is_authenticated)
):
    """获取用户的项目权限列表"""
    # 检查用户是否存在
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取用户的项目角色信息
    project_roles = await ProjectRole.filter(user_id=user_id).prefetch_related("project", "role")
    
    result = []
    for pr in project_roles:
        # 获取角色的权限列表
        permissions = await Permission.filter(
            roles__role_id=pr.role.id
        ).values_list("code", flat=True)
        
        result.append(UserProjectRole(
            project_id=pr.project.id,
            project_name=pr.project.name,
            role_id=pr.role.id,
            role_name=pr.role.name,
            role_level=pr.role.level,
            permissions=list(permissions)
        ))
    
    return result


@router.post("/check-permission", summary="检查用户权限")
async def check_user_permission(
    permission_check: UserPermissionCheck,
    user_info: dict = Depends(is_authenticated)
):
    """检查用户权限"""
    user_id = user_info.get('id')
    
    # 超级管理员拥有所有权限
    user = await User.get_or_none(id=user_id)
    if user and user.is_superuser:
        return {"has_permission": True, "reason": "超级管理员"}
    
    # 如果没有指定项目，检查系统级权限
    if permission_check.project_id is None:
        # 检查是否为系统管理员
        system_role = await Role.get_or_none(level=1)  # 系统管理员
        if system_role:
            has_role = await ProjectRole.filter(
                user_id=user_id,
                role_id=system_role.id
            ).exists()
            if has_role:
                # 检查系统管理员角色是否有该权限
                has_permission = await RolePermission.filter(
                    role_id=system_role.id,
                    permission__code=permission_check.permission_code
                ).exists()
                if has_permission:
                    return {"has_permission": True, "reason": "系统管理员"}
        
        # 系统级权限不能通过项目角色获得
        return {"has_permission": False, "reason": "系统级权限不足"}
    
    # 检查项目级权限
    if permission_check.project_id:
        project_role = await ProjectRole.filter(
            user_id=user_id,
            project_id=permission_check.project_id
        ).prefetch_related("role").first()
        
        if project_role:
            # 检查角色是否有该权限
            has_permission = await RolePermission.filter(
                role_id=project_role.role.id,
                permission__code=permission_check.permission_code
            ).exists()
            
            if has_permission:
                return {"has_permission": True, "reason": f"项目角色: {project_role.role.name}"}
    
    return {"has_permission": False, "reason": "权限不足"}