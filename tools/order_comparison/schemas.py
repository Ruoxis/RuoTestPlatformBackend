# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：schemas
@Time ：2025/9/15 9:56
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""

from typing import Optional
from fastapi import UploadFile
from pydantic import BaseModel, Field, model_validator
from pydantic import BaseModel, Field, validator
from enum import Enum


class HostType(str, Enum):
    """
    't': 'http://192.168.2.197',  # 测试环境的计料系统数据获取
    'f': 'http://mrp.sogal.net',  # 工厂正式环境
    'g': 'http://192.168.2.197',  # 工厂正式环境
    """
    T = 't'
    F = 'f'
    G = 'g'


class OrderInfo(BaseModel):
    order_id: str = Field(description="订单号")
    host: HostType = Field(description="订单时间，只能选择 t、f、g")


class OrderComparatorForm(BaseModel):
    """
    filter_column
    StockUpType, Code, Name, Color, Height, Width, Length, Quantity, Remark, EdgeBanding
    '物料类型', '物料编码', '名称', '花色', '高', '成品宽', '成品长', '数量', '备注','封边'
    """
    order_info_old: OrderInfo = Field(description="旧订单号")
    order_info_new: OrderInfo = Field(description="新订单号")
    filter_column: list | None = Field(description="需要过滤的字段",
                                       default=['StockUpType', 'Code', 'Name', 'Color', 'Height', 'Width', 'Length',
                                                'Quantity', 'Remark', 'EdgeBanding'])


class OrderComparatorResponse(BaseModel):
    comparison: list = Field(description="数据信息")
    stats: dict = Field(description="差异信息")
    install_area: dict | None = Field(description="安装面积", default={})


class NHAIHostType(str, Enum):
    """
    'test':  # NH-AI测试环境
    'dev':  # NH-AI开发环境
    'data':  # NH-AI数据环境
    """
    NH_TEST = 'test'
    NH_DEV = 'dev'
    NH_DATA = 'data'


class HostAreaType(str, Enum):
    """
    't':  # 综合服务平台地址
    'f':  # 经销商服务平台地址
    'p':  # PRE环境综合服务平台地址
    'm':  # 木门综合服务平台地址
    'test':  # NH-AI测试环境
    'dev':  # NH-AI开发环境
    'data':  # NH-AI数据环境
    """
    T = 't'
    F = 'f'
    P = 'p'
    M = 'm'
    NH_TEST = 'test'
    NH_DEV = 'dev'
    NH_DATA = 'data'


class CategoryType(int, Enum):
    """
    产品分类类型
    0: 衣柜 (cabinet)
    1: 橱柜 (cupboard)
    2: 木门 (door)
    """
    CABINET = 0
    CUPBOARD = 1
    DOOR = 2


class OrderAreaInfo(BaseModel):
    order_id: str = Field(description="订单号")
    host: HostAreaType = Field(description="订单时间，只能选择 t、f、p、m、test、dev、data")
    category_type: CategoryType = Field(description="产品分类类型，只能选择 0(衣柜)、1(橱柜)、2(木门)", default=0)


class OrderInstallArea(BaseModel):
    """
    示例数据：
    """
    order_info_old: OrderAreaInfo = Field(description="旧订单号")
    order_info_new: OrderAreaInfo = Field(description="新订单号")
    area_type: int = Field(description="方数类型 1(投影安装)、2(安装折合)")


class OrderTag(BaseModel):
    """
    示例数据：
    """
    order_info_old: OrderAreaInfo = Field(description="旧订单号")
    order_info_new: OrderAreaInfo = Field(description="新订单号")
    tag_name: str | None = Field(description="订单标识")
    tag_type: bool | None = Field(description="订单标识类型", default=False)


class OrderQuotation(BaseModel):
    """
    示例数据：
    """
    order_info_old: OrderAreaInfo = Field(description="旧订单号")
    order_info_new: OrderAreaInfo = Field(description="新订单号")
    code_key: str | None = Field(description="报价编码")
    filter_column: list | None = Field(description="需要过滤的字段",
                                       default=['materialType', 'code', 'name', 'length', 'width', 'thickness',
                                                'quantity', 'speac', 'area',
                                                'colorCode', 'colorName', 'unit', 'depthRate', 'priceRate', 'bodyNo',
                                                'linearMeterRate',
                                                'priceFlag', 'quotationType', 'remark'])


class OrderQuotationToC(BaseModel):
    host: NHAIHostType = Field(description="NH-AI环境，只能选择 test、dev、data", default=NHAIHostType.NH_TEST)
    order_id: str = Field(description="订单号", default="L02490125000040")
    filter_column: Optional[list] = Field(description="需要过滤的字段",
                                          default=['prodNum', 'prodName', 'quoteType', 'prodType', 'length', 'width',
                                                   'height', 'area', 'number', 'unit', 'color', 'spec', 'comments'])

    # 移除 UploadFile 字段，改用字符串标识
    file_type: Optional[str] = Field(None, description="文件类型: 'json' 或 'excel'")

    @model_validator(mode='after')
    def validate_data_input(cls, values):
        """验证文件类型"""
        file_type = values.file_type

        if file_type and file_type not in ['json', 'excel']:
            raise ValueError('file_type 只能是 "json" 或 "excel"')

        return values


if __name__ == '__main__':
    pass
