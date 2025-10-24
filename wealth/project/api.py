from fastapi import APIRouter, HTTPException, Depends, status
from auth.permission.decorators import require_permission
from .schemas import AddProjectForm, UpdateProjectForm, ProjectSchemas, ProjectListSchemas
from .models import Project
from auth.user.models import User
from auth.auth import is_authenticated

# 创建路由对象，添加用户鉴权
router = APIRouter(tags=["项目管理"], dependencies=[Depends(is_authenticated)])


# 创建项目
@router.post("/project", summary="创建项目", status_code=status.HTTP_201_CREATED, response_model=ProjectSchemas)
@require_permission("project:create")
async def create_project(item: AddProjectForm, user_info: dict = Depends(is_authenticated)):
    # 获取当前登录用户的信息
    user = await User.get_or_none(id=user_info['id'])
    if not user:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用户不存在")
    # 创建项目，关联用户
    project = await Project.create(name=item.name, user=user, username=user.nickname)
    return project


# 获取项目列表
@router.get("/project", summary="项目列表", response_model=ProjectListSchemas, status_code=status.HTTP_200_OK)
async def get_projects(page: int = 1, size: int = 10):
    # 获取项目列表
    query = Project.all().order_by("-id")
    # 获取数量总量
    total = await query.count()
    projects = await query.offset((page - 1) * size).limit(size)
    result = []
    for project in projects:
        result.append(ProjectSchemas(**project.__dict__))
    return {"total": total, "data": result}


# 获取单个项详情
@router.get("/project/{project_id}", summary="项目详情", response_model=ProjectSchemas, status_code=status.HTTP_200_OK)
async def get_projects(project_id: int):
    # 获取项目单个项详情
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="项目不存在")
    return project


# 删除项目
@router.delete("/project/{project_id}", summary="删除项目", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("project:delete", "project_id")
async def delete_project(project_id: int, user_info: dict = Depends(is_authenticated)):
    # 获取项目
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="项目不存在")
    await project.delete()


# 修改项目名称
@router.put("/project/{project_id}", summary="修改项目", response_model=ProjectSchemas, status_code=status.HTTP_200_OK)
@require_permission("project:update", "project_id")
async def update_project(project_id: int, item: UpdateProjectForm, user_info: dict = Depends(is_authenticated)):
    # 获取项目列表
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="项目不存在")
    project.name = item.name
    await project.save()
    return project
