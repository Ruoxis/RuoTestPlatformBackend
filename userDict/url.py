# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：url
@Time ：2025/7/24 18:01
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from fastapi import APIRouter, HTTPException, Depends, status
from tortoise.expressions import Q

from auth.auth import is_authenticated
from .models import FunctionDict
from .schemas import (FunctionDictList, FunctionDictBase
                      )

router = APIRouter(dependencies=[Depends(is_authenticated)])


@router.get("/functionDict", summary="获取函数字典列表", response_model=FunctionDictList)
async def get_function_dict_list(page: int = 1, size: int = 10, dict_type: str = None, search: str = None):
    """
    获取函数字典列表
    - fun_type: 函数类型(before/after/public)
    - search: 搜索函数名称或描述
    """
    # 这里应该是从数据库查询的逻辑，示例中使用模拟数据
    query = FunctionDict.all().order_by("class_name")
    # 过滤逻辑
    print(dict_type)
    if dict_type:
        query = query.filter(dict_type__icontains=dict_type)
    if search:
        query = query.filter(Q(dict_name__icontains=search) | Q(fun_desc__icontains=search))

    # 分页逻辑
    dict_list = await query.offset((page - 1) * size).limit(size)
    total = await query.count()
    function_dicts = [FunctionDictBase.from_orm(item) for item in dict_list]
    return {
        "total": total,
        "data": function_dicts
    }


@router.get("/functionDict/{func_id}", summary="获取单个函数详情", response_model=FunctionDictBase)
async def get_function_dict_detail(func_id: int):
    """获取单个函数详情"""
    # 这里应该是从数据库查询的逻辑，示例中使用模拟数据
    query = await FunctionDict.filter(id=func_id).first()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接口信息不存在"
        )
    return FunctionDictBase.from_orm(query)


# @router.post("/functionDict", summary="创建函数字典", status_code=status.HTTP_201_CREATED,
#              response_model=FunctionDictBase)
# async def create_function_dict(item: AddFunctionDictForm = AddFunctionDictForm.depends()):
#     """创建函数字典"""
#     if isinstance(item, dict):  # 处理验证失败的情况
#         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))
#
#     # 这里应该是保存到数据库的逻辑，示例中返回模拟数据
#     mock_data = {
#         "id": 3,
#         **item.model_dump(),
#         "create_time": datetime.now(),
#         "update_time": None
#     }
#     return FunctionDictBase(**mock_data)
#
#
# @router.put("/functionDict/{func_id}", summary="更新函数字典", response_model=FunctionDictBase)
# async def update_function_dict(func_id: int, item: UpdateFunctionDictForm = UpdateFunctionDictForm.depends()):
#     """更新函数字典"""
#     if isinstance(item, dict):  # 处理验证失败的情况
#         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))
#
#     # 这里应该是更新数据库的逻辑，示例中返回模拟数据
#     mock_data = {
#         "id": func_id,
#         **item.model_dump(),
#         "create_time": datetime.now(),
#         "update_time": datetime.now()
#     }
#     return FunctionDictBase(**mock_data)
#
#
# @router.delete("/functionDict/{func_id}", summary="删除函数字典", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_function_dict(func_id: int):
#     """删除函数字典"""
#     # 这里应该是从数据库删除的逻辑
#     return


if __name__ == '__main__':
    pass
