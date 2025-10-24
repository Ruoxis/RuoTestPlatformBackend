# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：api
@Time ：2025/9/15 9:55
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""

from io import BytesIO
from tools.src.get_order_data import get_data_for_only
from tools.src.get_service_platform_data import AreaData, TagData, QuotationData
from tools.src.order_comparator import OrderComparator
from tools.src.get_toc_product_price import TocProductPrice
from .order_comparison.schemas import *
from fastapi import Depends, HTTPException, status, APIRouter
from auth.auth import is_authenticated

router = APIRouter(tags=['辅助工具'], dependencies=[Depends(is_authenticated)])


@router.post("/order_comparison", tags=['计料数据对比'], summary="计料数据对比", status_code=status.HTTP_201_CREATED,
             response_model=OrderComparatorResponse)
async def order_comparison(item: OrderComparatorForm):
    try:
        new_info = get_data_for_only(item.order_info_new.host, item.order_info_new.order_id, item.filter_column)
        old_info = get_data_for_only(item.order_info_old.host, item.order_info_old.order_id, item.filter_column)
        if new_info is None or old_info is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"{item.order_info_old.order_id if old_info is None else item.order_info_new.order_id}未获取到数据")

        oc = OrderComparator(old_info.get(item.order_info_old.order_id), new_info.get(item.order_info_new.order_id))
        return OrderComparatorResponse(**oc.compare_json_data())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/area_comparison", tags=['安装折合数据对比'], summary="安装折合数据对比",
             status_code=status.HTTP_201_CREATED, response_model=OrderComparatorResponse)
async def order_install_area_comparison(item: OrderInstallArea):
    """
    a = {
        "order_info_old": {
            "order_id": "2024010112345678",
            "host": "t",
            "category_type": 0
        },
        "order_info_new": {
            "order_id": "2024010112345679",
            "host": "t",
            "category_type": 0
        },
        "area_type": 1
    }
    """

    try:
        old_service_data = AreaData(host=item.order_info_old.host, area=item.area_type,
                                    opty_id=item.order_info_old.order_id,
                                    category_type=item.order_info_old.category_type)
        new_service_data = AreaData(host=item.order_info_new.host, area=item.area_type,
                                    opty_id=item.order_info_new.order_id,
                                    category_type=item.order_info_new.category_type)
        old_result = old_service_data.get_order_install_area()
        new_result = new_service_data.get_order_install_area()
        print(old_result)
        print(new_result)
        if old_result is None or new_result is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f" {item.order_info_old.order_id if old_result is None else item.order_info_new.order_id}未获取到数据")

        comparator = OrderComparator(old_result.get("install"), new_result.get("install"), key_field="productName",
                                     exclude_fields=['Code', "productName"], name_field="productName")
        comparator_result = comparator.compare_json_data()
        comparator_result["install_area"] = {
            "old": old_result.get("install_area"),
            "new": new_result.get("install_area"),
            "diff": old_result.get("install_area") == new_result.get("install_area")
        }
        return OrderComparatorResponse(**comparator_result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/tag_comparison", tags=['标签数据对比'], summary="标签数据对比",
             status_code=status.HTTP_201_CREATED, response_model=OrderComparatorResponse)
async def order_tag_comparison(item: OrderTag):
    """
    {
      "order_info_old": {
          "order_id": "L0040012500655-81",
          "host": "test",
          "category_type": 0
      },
      "order_info_new": {
          "order_id": "L0040012300795-22",
          "host": "t",
          "category_type": 0
      },
      "tag_name": None
    }
    """

    try:
        tage_name = item.tag_name
        if tage_name is None:
            tage_name = ""
        if item.tag_type:
            exclude_fields = []
        else:
            exclude_fields = ["signType"]

        old_service_data = TagData(host=item.order_info_old.host,
                                   tage_name=tage_name,
                                   opty_id=item.order_info_old.order_id,
                                   category_type=item.order_info_old.category_type)
        new_service_data = TagData(host=item.order_info_new.host,
                                   tage_name=tage_name,
                                   opty_id=item.order_info_new.order_id,
                                   category_type=item.order_info_new.category_type)

        old_result = old_service_data.get_order_tag()
        new_result = new_service_data.get_order_tag()

        if old_result is None or new_result is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f" {item.order_info_old.order_id if old_result is None else item.order_info_new.order_id}未获取到数据")

        comparator = OrderComparator(old_result, new_result, key_field="signCode",
                                     name_field="signName", exclude_fields=exclude_fields)
        return OrderComparatorResponse(**comparator.compare_json_data())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/quotation_comparison", tags=['标签数据对比'], summary="标签数据对比",
             status_code=status.HTTP_201_CREATED, response_model=OrderComparatorResponse)
async def order_quotation_comparison(item: OrderQuotation):
    try:
        code_key = item.code_key
        if code_key is None:
            code_key = ""

        old_service_data = QuotationData(host=item.order_info_old.host,
                                         code_key=code_key,
                                         opty_id=item.order_info_old.order_id,
                                         category_type=item.order_info_old.category_type,
                                         filter_column=item.filter_column)
        new_service_data = QuotationData(host=item.order_info_new.host,
                                         code_key=code_key,
                                         opty_id=item.order_info_new.order_id,
                                         category_type=item.order_info_new.category_type,
                                         filter_column=item.filter_column)

        old_result = old_service_data.get_order_quotation()
        new_result = new_service_data.get_order_quotation()

        if old_result is None or new_result is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f" {item.order_info_old.order_id if old_result is None else item.order_info_new.order_id}未获取到数据")

        comparator = OrderComparator(old_result, new_result, key_field="code", name_field="name")
        return OrderComparatorResponse(**comparator.compare_json_data())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


from fastapi import UploadFile, File, Form
import json


@router.post("/toc_price_comparison", tags=['TOC报价数据对比'], summary="TOC报价数据对比",
             status_code=status.HTTP_201_CREATED, response_model=OrderComparatorResponse)
async def toc_price_comparison(host: str = Form(...),
                               order_id: str = Form(...),
                               filter_column: str = Form(default='[]'),
                               json_file: UploadFile = File(...),  # 改为必填
                               excel_file: UploadFile = File(...)  # 改为必填
                               ):
    """
    TOC报价数据对比接口 - 需要同时上传JSON和Excel文件

    示例调用：
    ```bash
    curl -X POST "http://localhost:8000/api/toc_price_comparison" \
      -F "host=test" \
      -F "order_id=L02490125000040" \
      -F "filter_column=['prodNum','prodName']" \
      -F "json_file=@/path/to/data.json" \
      -F "excel_file=@/path/to/data.xls"
    ```
    """
    try:
        # 验证两个文件都必须提供
        if not json_file or not excel_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须同时提供JSON和Excel文件"
            )

        # 解析filter_column
        try:
            filter_columns = json.loads(filter_column)
        except json.JSONDecodeError:
            filter_columns = ['prodNum', 'prodName', 'quoteType', 'prodType', 'length', 'width',
                              'height', 'area', 'number', 'unit', 'color', 'spec', 'comments']

        # 初始化TocProductPrice
        tpp = TocProductPrice(host=host)

        # 验证和处理JSON文件
        if not json_file.content_type or 'json' not in json_file.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请上传有效的JSON文件"
            )

        # 读取JSON文件内容 - 作为旧数据
        json_content = await json_file.read()
        json_data = BytesIO(json_content)

        # 从JSON文件获取旧数据
        nh_ai_data = tpp.get_nh_ai_price_data(json_data, order_id)
        new_result = tpp.extract_scheme_prices(nh_ai_data)

        # 验证和处理Excel文件
        valid_excel_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ]
        if excel_file.content_type not in valid_excel_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请上传有效的Excel文件"
            )

        # 读取Excel文件内容 - 作为新数据
        excel_content = await excel_file.read()
        excel_data = BytesIO(excel_content)

        # 从Excel提取新数据
        old_result = tpp.formatting_diy_price_data(excel_data)

        if not new_result:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="未从JSON文件中提取到有效的报价信息"
            )

        if not old_result:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="未从Excel文件中提取到有效的报价信息"
            )

        # 使用OrderComparator进行数据对比
        # JSON作为旧数据，Excel作为新数据
        comparator = OrderComparator(
            old_result,  # Excel数据作为新数据
            new_result,  # JSON数据作为旧数据
            key_field="prodNum",
            name_field="prodName",
            exclude_fields=filter_columns if filter_columns else None
        )

        return OrderComparatorResponse(**comparator.compare_json_data())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据处理失败: {str(e)}"
        )


if __name__ == '__main__':
    pass
