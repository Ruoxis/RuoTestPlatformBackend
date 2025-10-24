# 权限系统使用指南

## 系统概述

这是一个基于RBAC（基于角色的访问控制）的权限管理系统，专为测试平台设计。系统支持项目级权限控制，允许管理员为不同用户分配不同的项目角色，从而实现精细化的权限管理。

## 数据库表结构

权限系统新增了以下4个数据表：

1. **role** - 角色表
2. **permission** - 权限表
3. **role_permission** - 角色权限关联表
4. **project_role** - 用户项目角色表

## 快速开始

### 1. 初始化权限系统

```bash
# 推荐方式：使用快速初始化脚本
python permission/quick_init.py

# 或者使用迁移脚本
python permission/migration.py migrate

# 检查迁移状态
python permission/migration.py check
```

### 2. 运行测试

```bash
# 运行权限系统测试
python permission/test.py

# 运行完整部署
python permission/deploy.py
```

### 3. 注意事项

如果遇到 `ConfigurationError: default_connection for the model cannot be None` 错误，请使用 `quick_init.py` 而不是 `init_data.py`。

## 权限代码列表

### 项目管理权限
- `project:read` - 查看项目
- `project:update` - 更新项目
- `project:delete` - 删除项目

### 用例管理权限
- `case:create` - 创建用例
- `case:read` - 查看用例
- `case:update` - 更新用例
- `case:delete` - 删除用例

### 环境管理权限
- `env:create` - 创建环境
- `env:read` - 查看环境
- `env:update` - 更新环境
- `env:delete` - 删除环境

### 测试执行权限
- `test:run` - 执行测试
- `test:stop` - 停止测试
- `test:read` - 查看测试报告

### 配置管理权限
- `config:create` - 创建配置
- `config:read` - 查看配置
- `config:update` - 更新配置
- `config:delete` - 删除配置

### 成员管理权限
- `member:invite` - 邀请成员
- `member:remove` - 移除成员
- `member:update_role` - 更新成员角色

### 报告查看权限
- `report:read` - 查看报告
- `report:export` - 导出报告

### 数据导入导出权限
- `data:import` - 导入数据
- `data:export` - 导出数据

### 系统管理权限
- `system:manage` - 系统管理（超级管理员专用）

## 角色权限配置

### 1. 系统管理员
拥有所有权限，包括系统管理权限。

### 2. 项目管理员
拥有项目相关的所有权限：
- 项目管理：查看、更新、删除
- 用例管理：创建、查看、更新、删除
- 环境管理：创建、查看、更新、删除
- 测试执行：运行、停止、查看报告
- 配置管理：创建、查看、更新、删除
- 成员管理：邀请、移除、更新角色
- 报告查看：查看、导出
- 数据导入导出：导入、导出

### 3. 项目成员
拥有基本的项目操作权限：
- 项目管理：查看
- 用例管理：创建、查看、更新、删除（自己创建的）
- 环境管理：查看
- 测试执行：运行、查看报告
- 配置管理：查看
- 报告查看：查看、导出
- 数据导入导出：导出

### 4. 其他用户
拥有最基本的查看权限：
- 项目管理：查看
- 用例管理：查看
- 环境管理：查看
- 报告查看：查看

## API接口

### 权限管理相关接口

#### 1. 获取权限列表
```
GET /permission/permissions
```

#### 2. 获取角色列表
```
GET /permission/roles
```

#### 3. 获取角色权限
```
GET /permission/role/{role_id}/permissions
```

#### 4. 分配项目角色
```
POST /permission/project-role
{
    "user_id": 123,
    "project_id": 456,
    "role_id": 2
}
```

#### 5. 批量分配项目角色
```
POST /permission/project-role/batch
{
    "project_id": 456,
    "assignments": [
        {"user_id": 123, "role_id": 2},
        {"user_id": 124, "role_id": 3}
    ]
}
```

#### 6. 检查权限
```
POST /permission/check-permission
{
    "project_id": 456,
    "permission_code": "case:create"
}
```

#### 7. 获取用户项目权限
```
GET /permission/user/{user_id}/project/{project_id}/permissions
```

#### 8. 获取项目成员列表
```
GET /permission/project/{project_id}/members
```

## 工具脚本

### 1. 测试脚本
```bash
# 运行权限系统测试
python permission/test.py
```

### 2. 部署脚本
```bash
# 完整部署权限系统
python permission/deploy.py
```

### 3. 迁移状态检查
```bash
# 检查权限系统迁移状态
python permission/migration.py check
```

## 集成指南

### 为新注册用户分配默认角色

在 `user/schemas.py` 的 `register_user` 函数中，新用户注册后自动分配"其他用户"角色：

```python
# 注册后为用户分配默认角色
from auth.permission import Role, ProjectRole

# 获取"其他用户"角色
other_user_role = await Role.get(name="其他用户")
# 这里可以为用户分配全局角色或等待项目级角色分配
```

### 在现有API中添加权限控制

#### 最小改动集成示例

假设你有一个现有的API：

```python
# 原始API（无权限控制）
@router.get("/api-cases/{case_id}")
async def get_api_case(case_id: int):
    return {"case_id": case_id, "name": "测试用例"}
```

添加权限控制（最小改动）：

```python
# 添加权限控制后的API
@router.get("/api-cases/{case_id}")
async def get_api_case_secure(
    case_id: int, 
    user_info: dict = Depends(is_authenticated)
):
    # 获取项目ID（根据实际业务逻辑）
    project_id = await get_project_id_from_case(case_id)
    
    # 权限检查
    if not await permission_service.has_permission(
        user_id=user_info['id'],
        project_id=project_id,
        permission_code="case:read"
    ):
        raise HTTPException(
            status_code=403, 
            detail="您没有查看此用例的权限"
        )
    
    return {"case_id": case_id, "name": "测试用例"}
```

## 使用示例

### 1. 为用户分配项目角色

```python
# 分配项目管理员角色
POST /permission/project-role
{
    "user_id": 123,
    "project_id": 456,
    "role_id": 2  # 项目管理员
}
```

### 2. 批量分配角色

```python
POST /permission/project-role/batch
{
    "user_ids": [123, 124, 125],
    "project_id": 456,
    "role_id": 3  # 项目成员
}
```

### 3. 检查权限

```python
POST /permission/check-permission
{
    "project_id": 456,
    "permission_code": "case:create"
}
```

## 集成指南

### 步骤1：为现有接口添加权限控制

找到需要添加权限控制的接口，使用 `@require_permission` 装饰器：

```python
# 原来的接口
@router.get("/project/{project_id}/cases")
async def get_cases(project_id: int):
    return await get_project_cases(project_id)

# 添加权限控制后的接口
@router.get("/project/{project_id}/cases")
@require_permission("case:read", "project_id")
async def get_cases(project_id: int, user_info: dict = Depends(is_authenticated)):
    return await get_project_cases(project_id)
```

### 步骤2：处理项目创建者自动成为项目管理员

在项目创建时，自动为创建者分配项目管理员角色：

```python
@router.post("/project")
async def create_project(project_data: ProjectCreate, user_info: dict = Depends(is_authenticated)):
   # 创建项目
   project = await create_project_logic(project_data)

   # 为创建者分配项目管理员角色
   from auth.permission import permission_service
   await permission_service.assign_role_to_user(
      user_id=user_info['id'],
      project_id=project.id,
      role_id=2,  # 项目管理员
      granted_by=user_info['id']
   )

   return project
```

### 步骤3：处理公开项目的只读权限

对于公开项目，允许"其他用户"查看：

```python
@router.get("/project/{project_id}/cases")
async def get_cases(project_id: int, user_info: dict = Depends(is_authenticated)):
    # 检查项目是否公开
    project = await get_project(project_id)
  
    if project.is_public:
        # 公开项目允许所有登录用户查看
        return await get_project_cases(project_id)
    else:
        # 私有项目需要权限检查
        has_permission = await permission_service.has_permission(
            user_id=user_info['id'],
            permission_code="case:read",
            project_id=project_id
        )
      
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有查看权限")
      
        return await get_project_cases(project_id)
```

## 注意事项

1. **向后兼容**：现有接口无需修改即可正常运行
2. **性能优化**：权限检查使用数据库索引，性能影响最小
3. **扩展性**：支持自定义角色和权限，满足未来需求
4. **安全性**：超级管理员拥有所有权限，确保系统可用性

## 故障排除

### 常见问题

1. **数据库连接错误**
   - 错误：`ConfigurationError: default_connection for the model cannot be None`
   - 解决：使用 `python permission/quick_init.py` 而不是 `python -m permission.init_data`

2. **权限检查失败**
   - 确保用户已正确分配项目角色
   - 检查项目ID和用户ID是否正确

3. **角色权限未生效**
   - 重新运行初始化脚本更新权限配置
   - 检查 `role_permission` 表中的关联关系

### 调试技巧

```python
# 检查用户权限
from auth.permission import permission_service

permissions = await permission_service.get_user_permissions(user_id=123, project_id=456)
print("用户权限:", permissions)

# 检查角色分配
from auth.permission import ProjectRole

roles = await ProjectRole.filter(user_id=123, project_id=456)
for role in roles:
   print(f"角色: {await role.role.name}")
```

### 数据库迁移

如果已有数据需要迁移，可以使用以下SQL：

```sql
-- 为现有用户分配默认角色
INSERT INTO project_role (user_id, project_id, role_id, granted_by, created_at, update_time)
SELECT u.id, p.id, 4, 1, NOW(), NOW()
FROM user u, project p
WHERE NOT EXISTS (
    SELECT 1 FROM project_role pr WHERE pr.user_id = u.id AND pr.project_id = p.id
);
```

## 系统状态总结

✅ **权限系统已完成**：
- 数据库表结构设计完成
- 权限模型和角色系统实现
- 权限检查和验证机制
- FastAPI路由和接口
- 测试脚本和部署工具
- 完整文档和使用示例
- 数据库连接问题修复

🚀 **使用步骤**：
1. **初始化**：运行 `python permission/quick_init.py`
2. **测试**：运行 `python permission/test.py`
3. **部署**：运行 `python permission/deploy.py`
4. **集成**：按照集成指南为现有API添加权限控制
5. **验证**：访问 `/docs` 查看权限相关API

📁 **已创建文件**：
- `models.py` - 数据库模型
- `schemas.py` - Pydantic模式
- `service.py` - 权限服务
- `decorators.py` - 权限装饰器
- `utils.py` - 工具类
- `routes.py` - API路由
- `init_data.py` - 初始化数据
- `migration.py` - 数据库迁移
- `test.py` - 测试脚本
- `deploy.py` - 部署脚本
- `examples.py` - 使用示例
- `quick_init.py` - 快速初始化工具
- `README.md` - 使用指南

权限系统已完全就绪，可以开始为测试平台添加权限控制功能！
