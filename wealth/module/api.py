from fastapi import APIRouter, HTTPException, Depends, status
from .schemas import ModuleSchemas, AddModuleForm, UpdateModuleForm
from .models import Module
from auth.auth import is_authenticated
from wealth.project.models import Project

# 创建路由对象
router = APIRouter(tags=['测试模块'], dependencies=[Depends(is_authenticated)])


# 创建测试模块
@router.post('/module', summary='创建模块', status_code=status.HTTP_201_CREATED, response_model=ModuleSchemas)
async def create_module(item: AddModuleForm):
    project = await Project.get_or_none(id=item.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的项目ID不存在")
    module = await Module.create(name=item.name, project=project, username=item.username)
    return module


# 获取测试模块列表
@router.get('/module', summary='模块列表', status_code=status.HTTP_200_OK)
async def get_module(project_id: int | None = None):
    query = Module.all().prefetch_related('suites').order_by("-id")
    if project_id:
        project_id = await Project.get_or_none(id=project_id)
        query = query.filter(project=project_id)
    # 数据进行分页
    data = []
    for module in await query:
        data.append({
            "id": module.id,
            "name": module.name,
            "username": module.username,
            "create_time": module.create_time,
            "update_time": module.update_time,
            "suites": await module.suites.all().count(),
        })
    return data


# 获取单个测试模块详情
@router.get('/module/{module_id}', summary='模块详情', status_code=status.HTTP_200_OK)
async def get_module(module_id: int):
    module = await Module.get_or_none(id=module_id).prefetch_related('suites')
    if not module:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="模块不存在")
    # 返回数据
    result = {
        "id": module.id,
        "name": module.name,
        "username": module.username,
        "create_time": module.create_time,
        "update_time": module.update_time,
        "suites": await module.suites.all()
    }
    return result


# 删除测试模块
@router.delete('/module/{module_id}', summary='删除模块', status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(module_id: int):
    module = await Module.get_or_none(id=module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="模块不存在")
    await module.delete()


# 修改测试模块
@router.put('/module/{module_id}', summary='修改模块', response_model=ModuleSchemas, status_code=status.HTTP_200_OK)
async def update_module(module_id: int, item: UpdateModuleForm):
    module = await Module.get_or_none(id=module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="模块不存在")
    module.name = item.name
    await module.save()
    return module
