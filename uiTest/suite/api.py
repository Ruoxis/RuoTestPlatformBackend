from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from wealth.project.models import Project
from wealth.module.models import Module
from uiTest.runner.models import SuiteRunRecord
from auth.auth import is_authenticated
from .schemas import AddSuiteForm, SuiteSchemas, UpdateSuiteForm, AddStepForm, StepSchemas, StepListSchemas, \
    UpdateCaseSortForm
from .models import Suite, Step
from uiTest.case.models import Case

# 创建路由对象
router = APIRouter(dependencies=[Depends(is_authenticated)])


# 创建测试套件
@router.post("/suite", tags=["测试套件"], summary="创建套件", status_code=status.HTTP_201_CREATED,
             response_model=SuiteSchemas)
async def create_suite(item: AddSuiteForm):
    """创建测试套件的接口"""
    project = await Project.get_or_none(id=item.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="项目不存在")
    module = await Module.get_or_none(id=item.modules_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="模块不存在")
    suite = await Suite.create(**item.model_dump(exclude_unset=True))
    return suite


# 查询测试套件列表
@router.get("/suite", tags=["测试套件"], summary="套件列表", status_code=status.HTTP_200_OK)
async def get_suite(project: int | None = None, modules: int | None = None, page: int = 1, size: int = 10, search=None):
    """查询测试套件列表的接口"""
    # 获取所有套件
    query = Suite.all().order_by("-id")
    project = await Project.get_or_none(id=project)
    module = await Module.get_or_none(id=modules)
    if project:
        query = query.filter(project=project)
    if module:
        query = query.filter(modules=module)
    if search:
        query = query.filter(name__icontains=search)
    # 进行分页
    api_suites = await query.offset((page - 1) * size).limit(size).prefetch_related("cases")
    total = await query.count()
    result = []
    for suite in api_suites:
        module = await suite.modules
        # 获取最近一次执行状态
        run_record = await SuiteRunRecord.filter(suite=suite.id).order_by("-id").first()
        status = run_record.status if run_record else '等待执行'
        # 获取套件下的用例
        result.append({
            "create_time": suite.create_time,
            "update_time": suite.update_time,
            "id": suite.id,
            "name": suite.name,
            "username": suite.username,
            "status": status,
            "suite_type": suite.suite_type,
            "case_count": len(suite.cases),
            "suite_step_count": len(suite.suite_setup_step),
            "module": module.name if module else "",
            "run_count": await SuiteRunRecord.filter(suite=suite.id).count()
        })
    return {"data": result, "total": total}


# 获取单个套件详情
@router.get("/suite/{suite_id}", tags=["测试套件"], summary="套件详情", response_model=SuiteSchemas,
            status_code=status.HTTP_200_OK)
async def get_suite_detail(suite_id: int):
    """获取单个套件详情的接口"""
    suite = await Suite.get_or_none(id=suite_id)
    if not suite:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="套件不存在")
    return suite


# 删除套件信息
@router.delete("/suite/{suite_id}", tags=["测试套件"], summary="删除套件", status_code=status.HTTP_204_NO_CONTENT)
async def delete_suite(suite_id: int):
    """删除套件信息的接口"""
    suite = await Suite.get_or_none(id=suite_id)
    if not suite:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="套件不存在")
    await suite.delete()


# 更新套件信息
@router.put("/suite/{suite_id}", tags=["测试套件"], summary="更新套件", response_model=SuiteSchemas,
            status_code=status.HTTP_200_OK)
async def update_suite(suite_id: int, item: UpdateSuiteForm):
    """更新套件信息的接口"""
    suite = await Suite.get_or_none(id=suite_id)
    if not suite:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="套件不存在")
    module = Module.get_or_none(id=item.modules_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="传入的模块id有误，修改的模块不存在")
    # 修改套件的信息
    await suite.update_from_dict(item.dict(exclude_unset=True))
    await suite.save()
    return suite


# 往套件中添加用例
@router.post("/suite/{suite_id}/case", tags=["套件用例"], summary="套件中添加用例", status_code=status.HTTP_201_CREATED,
             response_model=StepSchemas)
async def add_step(suite_id: int, item: AddStepForm):
    """往套件中添加用例的接口"""
    suite = await Suite.get_or_none(id=suite_id)
    if not suite:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="操作的套件不存在")
    case_ = await Case.get_or_none(id=item.cases_id)
    if not case_:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="操作的用例不存在")
    # sort = await Step.filter(suite=suite).count()
    # 往测试套件中添加用例
    suite = await Step.create(suite=suite, cases=case_, sort=item.sort)
    return suite


# 删除套件中的用例
@router.delete("/suite/{suite_id}/case/{case_id}", tags=["套件用例"], summary="删除套件中的用例",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_step(case_id: int, suite_id: int):
    """删除套件中的用例的接口"""
    step = await Step.get_or_none(id=case_id, suite_id=suite_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="操作的套件用例不存在")
    await step.delete()


# 获取套件中的所有用例
@router.get("/suite/{suite_id}/case", tags=["套件用例"], summary="获取套件中的用例", status_code=status.HTTP_200_OK,
            response_model=list[StepListSchemas])
async def get_step(suite_id: int):
    """获取套件中的所有用例的接口"""
    step = await Step.filter(suite_id=suite_id).prefetch_related("cases", 'suite').order_by('sort')
    result = []
    for i in step:
        item = {
            "id": i.id,
            "skip": i.skip,
            "sort": i.sort,
            "cases_id": i.cases.id,
            "suite_id": i.suite.id,
            "cases_name": i.cases.name,
            "suite_name": i.suite.name,
        }
        result.append(item)
    return result


# 套件中修改用例跳过执行
@router.put("/suite/{suite_id}/case/{case_id}", tags=["套件用例"], summary="修改是否跳过执行",
            status_code=status.HTTP_200_OK,
            response_model=StepSchemas)
async def update_step(case_id: int, suite_id: int):
    """套件中修改用例跳过执行"""
    step = await Step.get_or_none(id=case_id, suite_id=suite_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="操作的套件用例不存在")
    step.skip = not step.skip
    await step.save()
    return step


# 修改用例执行的顺序
@router.post("/suite/{suite_id}/case/sort", tags=["套件用例"], summary="修改用例执行的顺序",
             status_code=status.HTTP_200_OK)
async def update_sort(suite_id: int, item: List[UpdateCaseSortForm]):
    """修改用例执行的顺序"""
    for i in item:
        step = await Step.get(id=i.id, suite_id=suite_id)
        step.sort = i.sort
        await step.save()
    return await Step.filter(suite_id=suite_id).order_by('sort')
