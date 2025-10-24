"""
权限系统使用示例
展示如何在现有代码中集成权限控制
"""

# 示例1: 在现有API中使用权限装饰器
from fastapi import APIRouter, Depends, HTTPException
from auth.permission.decorators import require_permission
from auth.permission.utils import permission_service

# 示例：项目相关的API
router = APIRouter()

@router.get("/projects/{project_id}")
@require_permission("project:read")
async def get_project(project_id: int, user_id: int = Depends(get_current_user_id)):
    """获取项目信息 - 需要project:read权限"""
    # 权限已通过装饰器检查
    return {"project_id": project_id, "name": "示例项目"}

@router.post("/projects")
@require_permission("project:create")
async def create_project(project_data: dict, user_id: int = Depends(get_current_user_id)):
    """创建新项目 - 需要project:create权限"""
    # 权限已通过装饰器检查
    return {"id": 1, "name": project_data.get("name")}

@router.put("/projects/{project_id}")
@require_permission("project:update")
async def update_project(project_id: int, project_data: dict, user_id: int = Depends(get_current_user_id)):
    """更新项目 - 需要project:update权限"""
    # 权限已通过装饰器检查
    return {"message": "项目更新成功"}

@router.delete("/projects/{project_id}")
@require_permission("project:delete")
async def delete_project(project_id: int, user_id: int = Depends(get_current_user_id)):
    """删除项目 - 需要project:delete权限"""
    # 权限已通过装饰器检查
    return {"message": "项目删除成功"}


# 示例2: 在函数内部进行权限检查
async def check_user_can_edit_case(user_id: int, project_id: int, case_id: int):
    """检查用户是否可以编辑用例"""
    
    # 检查用户是否有项目级别的编辑权限
    has_permission = await permission_service.has_permission(
        user_id=user_id,
        project_id=project_id,
        permission_code="case:update"
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail="您没有编辑此用例的权限"
        )
    
    return True


# 示例3: 批量权限检查
async def get_user_permissions_for_project(user_id: int, project_id: int):
    """获取用户在项目中的所有权限"""
    
    permissions = await permission_service.get_user_permissions(
        user_id=user_id,
        project_id=project_id
    )
    
    return {
        "user_id": user_id,
        "project_id": project_id,
        "permissions": permissions,
        "role": await permission_service.get_user_role_in_project(user_id, project_id)
    }


# 示例4: 动态权限控制
async def can_user_access_resource(user_id: int, project_id: int, resource_type: str, action: str):
    """动态检查用户是否可以访问特定资源"""
    
    permission_code = f"{resource_type}:{action}"
    
    return await permission_service.has_permission(
        user_id=user_id,
        project_id=project_id,
        permission_code=permission_code
    )


# 示例5: 在现有API中集成权限控制（最小改动）
from fastapi import Request

# 原始API（无权限控制）
@router.get("/api-cases/{case_id}")
async def get_api_case(case_id: int):
    """原始API - 无权限控制"""
    return {"case_id": case_id, "name": "测试用例"}

# 添加权限控制后的API（最小改动）
@router.get("/api-cases/{case_id}")
async def get_api_case_secure(case_id: int, request: Request):
    """添加权限控制后的API"""
    
    # 从请求中获取用户信息（假设已通过JWT中间件验证）
    user_id = request.state.user_id
    project_id = await get_project_id_from_case(case_id)
    
    # 权限检查
    if not await permission_service.has_permission(
        user_id=user_id,
        project_id=project_id,
        permission_code="case:read"
    ):
        raise HTTPException(
            status_code=403,
            detail="您没有查看此用例的权限"
        )
    
    return {"case_id": case_id, "name": "测试用例"}


# 示例6: 权限管理API的使用示例
async def assign_project_role_example():
    """为用户分配项目角色的示例"""
    
    from auth.permission.models import Role, ProjectRole
    
    # 获取项目管理员角色
    project_admin_role = await Role.get(name="项目管理员")
    
    # 分配角色给用户
    project_role = await ProjectRole.create(
        user_id=123,  # 目标用户ID
        project_id=456,  # 项目ID
        role_id=project_admin_role.id,
        granted_by=789  # 操作者ID
    )
    
    return project_role


# 示例7: 批量权限检查
async def check_multiple_permissions(user_id: int, project_id: int, permissions: list):
    """批量检查用户权限"""
    
    results = {}
    
    for perm in permissions:
        results[perm] = await permission_service.has_permission(
            user_id=user_id,
            project_id=project_id,
            permission_code=perm
        )
    
    return results


# 示例8: 前端集成示例
async def get_user_menu_permissions(user_id: int, project_id: int):
    """获取用户在前端可见的菜单权限"""
    
    menu_permissions = {
        "project": {
            "can_read": await permission_service.has_permission(user_id, project_id, "project:read"),
            "can_create": await permission_service.has_permission(user_id, project_id, "project:create"),
            "can_update": await permission_service.has_permission(user_id, project_id, "project:update"),
            "can_delete": await permission_service.has_permission(user_id, project_id, "project:delete")
        },
        "case": {
            "can_read": await permission_service.has_permission(user_id, project_id, "case:read"),
            "can_create": await permission_service.has_permission(user_id, project_id, "case:create"),
            "can_update": await permission_service.has_permission(user_id, project_id, "case:update"),
            "can_delete": await permission_service.has_permission(user_id, project_id, "case:delete")
        },
        "environment": {
            "can_read": await permission_service.has_permission(user_id, project_id, "environment:read"),
            "can_create": await permission_service.has_permission(user_id, project_id, "environment:create"),
            "can_update": await permission_service.has_permission(user_id, project_id, "environment:update"),
            "can_delete": await permission_service.has_permission(user_id, project_id, "environment:delete")
        }
    }
    
    return menu_permissions


# 示例9: 权限缓存使用示例
async def get_cached_user_permissions(user_id: int, project_id: int):
    """使用缓存获取用户权限（提高性能）"""
    
    cache_key = f"user_permissions:{user_id}:{project_id}"
    
    # 这里可以集成Redis缓存
    # cached_permissions = await redis.get(cache_key)
    # if cached_permissions:
    #     return cached_permissions
    
    # 从数据库获取
    permissions = await permission_service.get_user_permissions(user_id, project_id)
    
    # 缓存结果（可选）
    # await redis.setex(cache_key, 300, json.dumps(permissions))  # 缓存5分钟
    
    return permissions


# 示例10: 权限日志记录示例
async def log_permission_check(user_id: int, project_id: int, permission_code: str, result: bool):
    """记录权限检查日志"""
    
    # 可以集成日志系统
    log_data = {
        "user_id": user_id,
        "project_id": project_id,
        "permission_code": permission_code,
        "result": result,
        "timestamp": "2024-01-01 12:00:00"
    }
    
    # 实际使用时可以写入日志文件或发送到日志服务
    # logger.info(f"权限检查: {log_data}")


# 实用工具函数
async def get_project_id_from_case(case_id: int):
    """从用例ID获取项目ID（示例实现）"""
    # 实际项目中需要根据数据库结构实现
    return 1


async def get_current_user_id():
    """获取当前用户ID（示例实现）"""
    # 实际项目中需要从JWT token或session中获取
    return 1


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        """运行示例"""
        
        # 示例：检查用户权限
        user_id = 1
        project_id = 1
        
        permissions = await get_user_permissions_for_project(user_id, project_id)
        print("用户权限:", permissions)
        
        # 示例：批量权限检查
        perms_to_check = ["project:read", "case:create", "environment:update"]
        results = await check_multiple_permissions(user_id, project_id, perms_to_check)
        print("批量权限检查结果:", results)
    
    # 运行示例
    asyncio.run(main())