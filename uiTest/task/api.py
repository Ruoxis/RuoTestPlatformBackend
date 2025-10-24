from fastapi import APIRouter, HTTPException, Depends, status
from wealth.project.models import Project
from uiTest.runner.models import TaskRunRecord
from uiTest.suite.models import Suite
from .schemas import AddTaskForm, TaskSchemas, UpdateTaskForm, AddSuiteToTaskForm, TaskDetailSchemas
from .models import Task
from auth.auth import is_authenticated

router = APIRouter(tags=['测试计划'], dependencies=[Depends(is_authenticated)])


# 创建测试计划
@router.post("/task", summary="创建任务", response_model=TaskSchemas, status_code=status.HTTP_201_CREATED)
async def create_task(item: AddTaskForm):
    try:
        project = await Project.get_or_none(id=item.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的项目ID不存在")
        task_type = item.task_type
        if task_type == 0:
            task = await Task.create(**item.model_dump())
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="任务类型错误")
        return task
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# 获取测试计划列表
@router.get("/task", summary="任务列表", status_code=status.HTTP_200_OK)
async def get_task(page: int = 1, size: int = 10, search=None, task_type: int = None, project_id: int = None):
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的项目ID不存在")

    # 分别构建UI和API任务的查询
    ui_query = Task.filter(project_id=project_id).prefetch_related("suites")

    # 添加搜索条件
    if search:
        ui_query = ui_query.filter(name__icontains=search)

    # 根据任务类型过滤
    if task_type == 0:  # 只查询UI任务
        total_count = await ui_query.count()
        paginated_tasks = await ui_query.offset((page - 1) * size).limit(size).order_by("-create_time")
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的任务类型错误")

    result = []
    # 处理所有任务
    for task in paginated_tasks:
        # 更准确的任务类型判断
        run_record = await TaskRunRecord.filter(task=task.id).order_by("-id").first()
        run_count = await TaskRunRecord.filter(task=task.id).count()

        # 获取套件数量
        suites_count = len(task.suites) if hasattr(task, 'suites') and task.suites else 0

        result.append({
            "id": task.id,
            "name": task.name,
            "username": task.username,
            "status": run_record.status if run_record else '等待执行',
            "task_type": task.task_type,
            "create_time": task.create_time,
            "update_time": task.update_time,
            "suites_count": suites_count,
            "run_count": run_count
        })

    return {
        "data": result,
        "total": total_count
    }


# /api/task/${taskId}?task_type=${taskType}
# 删除测试计划
@router.delete("/task/{task_id}/{task_type}", summary="删除任务", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, task_type: int = None):
    try:
        if task_type == 0:
            task = await Task.get_or_none(id=task_id)
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的任务类型错误")
        if not task:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的任务ID不存在")
        await task.delete()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# 修改测试计划名称
@router.put("/task/{task_id}", summary="修改任务", response_model=TaskSchemas, status_code=status.HTTP_200_OK)
async def update_task(task_id: int, item: UpdateTaskForm):
    try:
        if item.task_type == 0:
            task = await Task.get_or_none(id=task_id)
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的任务类型错误")
        if not task:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的任务ID不存在")
        task.name = item.name
        await task.save()
        return task
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# 往任务中添加业务流试(套件)
@router.post("/task/{task_id}/suite", tags=['测试计划'], summary="任务中添加套件", status_code=status.HTTP_201_CREATED,
             response_model=TaskSchemas)
async def add_step(task_id: int, item: AddSuiteToTaskForm):
    try:
        if item.task_type == 0:
            task = await Task.get_or_none(id=task_id)
            suite = await Suite.get_or_none(id=item.suite_id)
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的任务类型错误")

        if not task or not suite:
            mgs = "传入的任务类型错误" if not task else "任务不存在"
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=mgs)

        # 往多对多的关联字段中添加数据
        await task.suites.add(suite)
        return task
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# 删除任务中的业务流(套件)
@router.delete("/task/{task_id}/suite/{suite_id}/{task_type}", summary="删除任务中套件",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_step(task_id: int, suite_id: int, task_type: int = None):
    try:
        if task_type == 0:
            task = await Task.get_or_none(id=task_id)
            suite = await Suite.get_or_none(id=suite_id)
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的任务类型错误")

        if not task or not suite:
            mgs = "传入的任务类型错误" if not task else "任务不存在"
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=mgs)

        # 往多对多的关联字段中添加数据
        await task.suites.remove(suite)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# 获取测试计划详情(任务中所有的套件)
@router.get("/task/{task_id}", summary="任务详情", response_model=TaskDetailSchemas, status_code=status.HTTP_200_OK)
async def get_task_detail(task_id: int, task_type: int = None):
    try:
        if task_type == 0:
            task = await Task.get_or_none(id=task_id).prefetch_related("suites")

        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的任务类型错误")
        if not task:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="任务不存在")

        suite_list = []
        # 查询测试计划中所有的测试套件
        suites = await task.suites.all()
        # 遍历获取套件的名称和基本信息
        for su in suites:
            suite_list.append({
                "suite_id": su.id,
                "suite_name": su.name if task_type == 0 else su.suite_name,
                "suite_type": su.suite_type,
                "create_time": su.create_time,
                "update_time": su.update_time
            })
        # 准备返回的数据
        result = {
            "id": task.id,
            "name": task.name,
            "username": task.username,
            'create_time': task.create_time,
            "update_time": task.update_time,
            "suites": suite_list,
            "task_type": task.task_type
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
