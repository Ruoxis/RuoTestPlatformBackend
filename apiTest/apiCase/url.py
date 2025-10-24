# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：url
@Time ：2025/7/10 14:13
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""

from fastapi import APIRouter, HTTPException, Depends, status
from tortoise.expressions import Q

from auth.auth import is_authenticated
from .schemas import (
    ApiInfoSchema, AddApiInfoForm, UpdateApiInfoForm,
    ApiCaseSchema, AddApiCaseForm, UpdateApiCaseForm, ApiInfoStatusForm, ApiInfoList, ApiInfoDebugSchema,
    ApiDebugResponse, ApiCaseList, ApiCaseStatusForm, CopyApiCaseForm, ApiCaseDebugSchema,
)
from .models import ApiInfo, ApiCase

router = APIRouter(dependencies=[Depends(is_authenticated)])


# -------------------- 接口信息相关API --------------------
@router.get("/info/{api_id}", summary="获取单个接口详情", response_model=ApiInfoSchema)
async def get_api_info_detail(api_id: int):
    """获取接口详情的接口"""
    api_info = await ApiInfo.filter(id=api_id).prefetch_related("project",
                                                                "create_user",
                                                                "update_user").first()
    if not api_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口信息不存在"
        )
    return await ApiInfoSchema.from_orm_with_relations(api_info)


@router.get("/info", summary="获取全部接口详情", response_model=ApiInfoList)
async def list_api_infos(page: int = 1, size: int = 10, search=None, project_id: int = None):
    """
    获取接口列表（批量优化查询）
    - 使用单个查询获取所有关联数据
    - 支持按项目ID过滤
    """
    query = ApiInfo.all().order_by("-create_time").prefetch_related("project", "create_user", "update_user")
    # 构建查询条件
    if search:
        query = query.filter(Q(api_name__icontains=search) | Q(api_module__icontains=search))
    if project_id:
        query = query.filter(project_id=project_id)
    api_info = await query.offset((page - 1) * size).limit(size)
    total = await query.count()
    return {
        "total": total,
        "data": await ApiInfoSchema.from_queryset(api_info)}


@router.post("/info", summary="创建接口信息", status_code=status.HTTP_201_CREATED, response_model=ApiInfoSchema)
async def create_api_info(item: AddApiInfoForm = AddApiInfoForm.depends()):
    """创建接口信息的接口"""
    if isinstance(item, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))

    api_info = await ApiInfo.create(**item.model_dump(exclude_unset=True))

    return ApiInfoSchema(**api_info.__dict__)


@router.post("/info/{case_id}", summary="复制接口信息", response_model=ApiInfoSchema,
             status_code=status.HTTP_201_CREATED)
async def copy_api_case(case_id: int, item: CopyApiCaseForm):
    """复制用例的接口"""
    api_info = await ApiInfo.get_or_none(id=case_id)
    if not api_info:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例不存在")
    # 复制用例
    api_info_data = AddApiInfoForm(**api_info.__dict__)
    api_info_data.api_name = api_info.api_name + "_副本"
    api_info_data.create_user_id = item.create_user_id
    new_case = await ApiInfo.create(**api_info_data.__dict__)

    return ApiInfoSchema(**new_case.__dict__)


@router.put("/info/{api_id}", summary="更新接口信息", response_model=ApiInfoSchema)
async def update_api_info(api_id: int, item: UpdateApiInfoForm = UpdateApiInfoForm.depends()):
    """更新接口信息的接口"""
    if isinstance(item, dict):  # 处理验证失败的情况
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))
    api_info = await ApiInfo.filter(id=api_id).prefetch_related("project",
                                                                "create_user",
                                                                "update_user").first()
    if not api_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口信息不存在"
        )
    update_data = item.model_dump(exclude_unset=True)
    await api_info.update_from_dict(update_data)
    await api_info.save()
    # 返回时包含用户信息
    return await ApiInfoSchema.from_orm_with_relations(api_info)


@router.put("/infoStatus/{api_id}", summary="更新接口状态", response_model=ApiInfoSchema)
async def update_info_status(api_id: int, item: ApiInfoStatusForm):
    """更新接口状态"""
    # 使用select_for_update()确保更新操作的原子性
    api_info = await ApiInfo.filter(id=api_id).select_for_update().prefetch_related(
        "project", "create_user", "update_user"
    ).first()

    if not api_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口信息不存在"
        )
    # 直接更新并刷新对象
    await api_info.update_from_dict(item.model_dump(exclude_unset=True))
    await api_info.save()

    # 刷新关联关系
    await api_info.fetch_related("project", "create_user", "update_user")

    return await ApiInfoSchema.from_orm_with_relations(api_info)


@router.delete("/info/{api_id}", summary="删除接口用例", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_case(api_id: int):
    """删除接口信息"""
    api_info = await ApiInfo.get_or_none(id=api_id)
    if not api_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口用例不存在"
        )
    await api_info.delete()


# 接口数据调试接口
@router.post("/infoDebug", summary="接口数据调试", response_model=ApiDebugResponse)
async def api_debug(item: ApiInfoDebugSchema):
    """接口数据调试"""
    print(item.model_dump())
    response_data = {
        'basicInfo': {
            'status': 205,
            'size': '54kb',
            'time': 120,
            'success': True
        },
        'headers': [
            {'key': 'Content-Type', 'value': 'application/json'},
            {'key': 'Server', 'value': 'nginx/1.18.0'}
        ],
        'body': {
            'id': 123,
            'name': '示例数据'
        }}
    # 转换json格式返回
    return ApiDebugResponse(**response_data)


# -------------------- 接口测试用例相关API --------------------
@router.get("/case/{case_id}", summary="获取单个接口用例详情", response_model=ApiCaseSchema)
async def get_api_case(case_id: int):
    """获取单个接口用例详情"""
    api_case = await ApiCase.filter(id=case_id).prefetch_related("project",
                                                                 "create_user",
                                                                 "update_user").first()
    if not api_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口信息不存在"
        )
    return await ApiCaseSchema.from_orm_with_relations(api_case)


@router.get("/case", summary="获取全部接口用例详情", response_model=ApiCaseList)
async def list_api_case(page: int = 1, size: int = 10, search=None, project_id: int = None):
    """获取全部接口用例详情（批量优化查询）"""
    query = ApiCase.all().order_by("-create_time").prefetch_related("project", "create_user", "update_user")
    if search:
        query = query.filter(
            Q(case_name__icontains=search) | Q(case_module__icontains=search) | Q(case_desc__icontains=search))
    if project_id:
        query = query.filter(project_id=project_id)
    api_cases = await query.offset((page - 1) * size).limit(size)
    total = await query.count()
    return {'total': total,
            "data": await ApiCaseSchema.from_queryset(api_cases)
            }


@router.post("/case", summary="创建接口用例", status_code=status.HTTP_201_CREATED, response_model=ApiCaseSchema)
async def create_api_case(item: AddApiCaseForm = AddApiCaseForm.depends()):
    """创建接口用例"""
    if isinstance(item, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))

    api_case = await ApiCase.create(**item.model_dump(exclude_unset=True))

    return ApiCaseSchema(**api_case.__dict__)


@router.post("/case/{case_id}", summary="复制接口用例", response_model=ApiCaseSchema,
             status_code=status.HTTP_201_CREATED)
async def copy_api_case(case_id: int, item: CopyApiCaseForm):
    """复制用例的接口"""
    cases = await ApiCase.get_or_none(id=case_id)
    if not cases:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例不存在")
    # 复制用例
    case_data = AddApiCaseForm(**cases.__dict__)
    case_data.case_name = cases.case_name + "_副本"
    case_data.create_user_id = item.create_user_id
    new_case = await ApiCase.create(**case_data.__dict__)

    return ApiCaseSchema(**new_case.__dict__)


@router.put("/case/{case_id}", summary="更新接口用例", status_code=status.HTTP_201_CREATED,
            response_model=ApiCaseSchema)
async def update_api_case(case_id: int, item: UpdateApiCaseForm = UpdateApiCaseForm.depends()):
    """更新接口用例"""
    if isinstance(item, dict):  # 处理验证失败的情况
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))
    api_case = await ApiCase.filter(id=case_id).prefetch_related("project",
                                                                 "create_user",
                                                                 "update_user").first()
    if not api_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口信息不存在"
        )
    update_data = item.model_dump(exclude_unset=True)
    await api_case.update_from_dict(update_data)
    await api_case.save()
    # 返回时包含用户信息
    return await ApiCaseSchema.from_orm_with_relations(api_case)


@router.put("/caseStatus/{case_id}", summary="更新接口状态", response_model=ApiCaseSchema)
async def update_api_case_status(case_id: int, item: ApiCaseStatusForm):
    """更新接口状态"""
    # 使用select_for_update()确保更新操作的原子性
    api_case = await ApiCase.filter(id=case_id).select_for_update().prefetch_related(
        "project", "create_user", "update_user"
    ).first()

    if not api_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口信息不存在"
        )
    # 直接更新并刷新对象
    await api_case.update_from_dict(item.model_dump(exclude_unset=True))
    await api_case.save()

    # 刷新关联关系
    await api_case.fetch_related("project", "create_user", "update_user")

    return await ApiCaseSchema.from_orm_with_relations(api_case)


@router.delete("/case/{case_id}", summary="删除接口用例", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_case(case_id: int):
    """删除接口用例"""
    api_case = await ApiCase.get_or_none(id=case_id)
    if not api_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口用例不存在"
        )
    await api_case.delete()


@router.post("/caseDebug", summary="接口数据调试", response_model=ApiDebugResponse)
async def api_debug(item: ApiCaseDebugSchema):
    """接口数据调试"""
    print(item.model_dump())
    response_data = {
        'basicInfo': {
            'status': 205,
            'size': '54kb',
            'time': 120,
            'success': True,
            'assert': True,
        },
        'headers': [
            {'key': 'Content-Type', 'value': 'application/json'},
            {'key': 'Server', 'value': 'nginx/1.18.0'}
        ],
        'body': {
            'id': 123,
            'name': '示例数据'
        }}
    # 转换json格式返回
    return ApiDebugResponse(**response_data)


# funList
@router.get("/funList", summary="获取用户函数词典")
async def user_fun_list(type: str = None, page: int = 1, size: int = 10, search=None):
    """接口数据调试"""
    print()
    response_data = [
        {
            "id": 1,
            "fun_name": "set_cookies",
            "fun_desc": "添加cookies",
            "fun_type": "before",
            "param": [{"paramName": "cookies", "explain": "请填入cookies json", 'must': True}],
        },
        {
            "id": 3,
            "fun_name": "set_new_time",
            "fun_desc": "请求数据添加当前时间参数",
            "fun_type": "before",
            "param": [{"paramName": "key", "explain": "请填入参数名称", 'must': True}]
        }, {
            "id": 2,
            "fun_name": "get_cache",
            "fun_desc": "读取缓存",
            "fun_type": "public",
            "param": [{"paramName": "key", "explain": "请填入参数名称", 'must': True}]
        }, {
            "id": 4,
            "fun_name": "set_cache",
            "fun_desc": "写入缓存",
            "fun_type": "public",
            "param": [{"paramName": "key", "explain": "请填入参数名称", 'must': True},
                      {"paramName": "value", "explain": "请填入数据值", 'must': True}]
        }
    ]
    return response_data


if __name__ == "__main__":
    pass
