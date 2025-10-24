from fastapi import APIRouter, HTTPException, Depends, status
from .schemas import EnvironmentSchemas, AddEnvironmentForm, UpdateEnvironmentForm
from .models import Environment
from auth.auth import is_authenticated
from wealth.project.models import Project

# 创建路由对象
router = APIRouter(tags=['测试环境'], dependencies=[Depends(is_authenticated)])


# 创建测试环境
@router.post('/environment', summary='创建环境', status_code=status.HTTP_201_CREATED, response_model=EnvironmentSchemas)
async def create_environment(item: AddEnvironmentForm):
    # 方式一
    # environment = await Environment.create(**item.model_dump())
    # 方式二
    # environment = await Environment.create(name=item.name, host=item.host, global_vars=item.global_vars,
    # project_id=item.project_id, username=item.username)
    # 方式三
    project = await Project.get_or_none(id=item.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="项目不存在")
    environment = await Environment.create(name=item.name, host=item.host, global_vars=item.global_vars,
                                           project=project, username=item.username)
    return environment


# 获取测试环境列表
@router.get('/environment', summary='环境列表', response_model=list[EnvironmentSchemas],
            status_code=status.HTTP_200_OK)
async def get_environments(project_id: int | None = None):
    query = Environment.all()
    if project_id:
        project = await Project.get_or_none(id=project_id)
        query = query.filter(project=project)
    environments = await query.order_by("-id")
    return environments


# 获取单个测试环境详情
@router.get('/environment/{environment_id}', summary='环境详情', response_model=EnvironmentSchemas,
            status_code=status.HTTP_200_OK)
async def get_environment(environment_id: int):
    environment = await Environment.get_or_none(id=environment_id)
    if not environment:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="环境不存在")
    return environment


# 删除测试环境
@router.delete('/environment/{environment_id}', summary='删除环境', status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(environment_id: int):
    environment = await Environment.get_or_none(id=environment_id)
    if not environment:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="环境不存在")
    await environment.delete()


# 修改测试环境
@router.put('/environment/{environment_id}', summary='修改环境', response_model=EnvironmentSchemas,
            status_code=status.HTTP_200_OK)
async def update_environment(environment_id: int, item: UpdateEnvironmentForm):
    environment = await Environment.get_or_none(id=environment_id)
    if not environment:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="环境不存在")
    # environment.name = item.name
    # environment.host = item.host
    # environment.global_vars = item.global_vars
    environment = await environment.update_from_dict(item.model_dump(exclude_unset=True))
    await environment.save()
    return environment
