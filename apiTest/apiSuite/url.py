# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：url
@Time ：2025/7/10 14:15
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from fastapi import APIRouter, HTTPException, Depends, status
from tortoise.expressions import Q
from apiTest.apiSuite.models import ApiTestSuite
from auth.auth import is_authenticated
from .schemas import (
    # ... existing imports
    ApiTestSuiteSchema, ApiTestSuiteList, AddApiTestSuiteBaseForm, AddApiTestSuiteForm, UpdateApiTestSuiteForm,
    ApiTestSuiteStatusForm, CopyApiTestSuiteForm
)

router = APIRouter(dependencies=[Depends(is_authenticated)])


# -------------------- 测试套件相关API --------------------
@router.get("/suite/{suite_id}", summary="获取单个测试套件详情", response_model=ApiTestSuiteSchema)
async def get_api_suite_detail(suite_id: int):
    """获取测试套件详情的接口"""
    api_suite = await ApiTestSuite.filter(id=suite_id).prefetch_related(
        "project", "create_user", "update_user"
    ).first()
    if not api_suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在"
        )
    return await ApiTestSuiteSchema.from_orm_with_relations(api_suite)


@router.get("/suite", summary="获取全部测试套件详情", response_model=ApiTestSuiteList)
async def list_api_suites(page: int = 1, size: int = 10, search=None, suite_type: str = None, project_id: int = None):
    """
    获取测试套件列表
    :param page: 页码
    :param size: 每页数量
    :param search: 搜索关键字
    :param suite_type: 套件类型
    :param project_id: 项目ID
    """
    query = ApiTestSuite.all().order_by("-create_time").prefetch_related("project", "create_user", "update_user")
    # 构建查询条件
    if search:
        query = query.filter(
            Q(suite_name__icontains=search) |
            Q(suite_module__icontains=search) |
            Q(suite_desc__icontains=search))
    if project_id:
        query = query.filter(project_id=project_id)
    if suite_type:
        query = query.filter(suite_type=suite_type)

    api_suites = await query.offset((page - 1) * size).limit(size)
    total = await query.count()

    return {
        "total": total,
        "data": await ApiTestSuiteSchema.from_queryset(api_suites)
    }


@router.post("/suiteBase", summary="创建测试套件", status_code=status.HTTP_201_CREATED,
             response_model=ApiTestSuiteSchema)
async def create_api_suite(item: AddApiTestSuiteBaseForm):
    """创建测试套件的接口"""
    if isinstance(item, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))

    api_suite = await ApiTestSuite.create(**item.model_dump(exclude_unset=True))
    return ApiTestSuiteSchema(**api_suite.__dict__)


@router.post("/suite", summary="创建测试套件", status_code=status.HTTP_201_CREATED, response_model=ApiTestSuiteSchema)
async def create_api_suite(item: AddApiTestSuiteForm = AddApiTestSuiteForm.depends()):
    """创建测试套件的接口"""
    if isinstance(item, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))

    api_suite = await ApiTestSuite.create(**item.model_dump(exclude_unset=True))
    return ApiTestSuiteSchema(**api_suite.__dict__)


@router.post("/suite/{suite_id}", summary="复制测试套件", response_model=ApiTestSuiteSchema,
             status_code=status.HTTP_201_CREATED)
async def copy_api_suite(suite_id: int, item: CopyApiTestSuiteForm):
    """复制测试套件的接口"""
    api_suite = await ApiTestSuite.get_or_none(id=suite_id)
    if not api_suite:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试套件不存在")

    # 复制套件
    suite_data = AddApiTestSuiteForm(**api_suite.__dict__)
    suite_data.suite_name = api_suite.suite_name + "_副本"
    suite_data.create_user_id = item.create_user_id
    new_suite = await ApiTestSuite.create(**suite_data.model_dump())

    return ApiTestSuiteSchema(**new_suite.__dict__)


@router.put("/suite/{suite_id}", summary="更新测试套件", response_model=ApiTestSuiteSchema)
async def update_api_suite(suite_id: int, item: UpdateApiTestSuiteForm = UpdateApiTestSuiteForm.depends()):
    """更新测试套件的接口"""
    if isinstance(item, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))

    api_suite = await ApiTestSuite.filter(id=suite_id).prefetch_related(
        "project", "create_user", "update_user"
    ).first()
    if not api_suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在"
        )

    update_data = item.model_dump(exclude_unset=True)
    await api_suite.update_from_dict(update_data)
    await api_suite.save()

    return await ApiTestSuiteSchema.from_orm_with_relations(api_suite)


@router.put("/suiteStatus/{suite_id}", summary="更新测试套件状态", response_model=ApiTestSuiteSchema)
async def update_api_suite_status(suite_id: int, item: ApiTestSuiteStatusForm):
    """更新测试套件状态"""
    api_suite = await ApiTestSuite.filter(id=suite_id).select_for_update().prefetch_related(
        "project", "create_user", "update_user"
    ).first()

    if not api_suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在"
        )

    await api_suite.update_from_dict(item.model_dump(exclude_unset=True))
    await api_suite.save()
    await api_suite.fetch_related("project", "create_user", "update_user")

    return await ApiTestSuiteSchema.from_orm_with_relations(api_suite)


@router.delete("/suite/{suite_id}", summary="删除测试套件", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_suite(suite_id: int):
    """删除测试套件"""
    api_suite = await ApiTestSuite.get_or_none(id=suite_id)
    if not api_suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在"
        )
    await api_suite.delete()


if __name__ == '__main__':
    pass
