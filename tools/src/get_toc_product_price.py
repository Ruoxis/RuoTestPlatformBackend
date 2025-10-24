# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：get_toc_product_price
@Time ：2025/9/23 10:00
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from pathlib import Path

import pandas as pd
from io import BytesIO

from tools.src.external_api.nh_ai_api import NeuroHomeApiOss



class TocProductPrice:
    """获取产品报价"""

    def __init__(self, host="test"):
        self.host = host

    def get_nh_ai_price_data(self, json_data, order_no) -> dict:
        """
        获取AI报价数据，支持文件路径、字节流或文件对象

        Args:
            json_data: 可以是文件路径(str/pathlib.Path)、字节流(bytes/BytesIO)或文件对象
            order_no: 订单号
        """
        nh_ai = NeuroHomeApiOss(host=self.host)

        # 根据输入类型处理数据
        if isinstance(json_data, (str, Path)):
            # 文件路径方式
            data = nh_ai.upload_scheme_from_price_query(
                json_file_path=json_data,
                order_no=order_no,
            )
        elif isinstance(json_data, (bytes, BytesIO)):
            # 字节流方式
            if isinstance(json_data, BytesIO):
                json_bytes = json_data.getvalue()
            elif hasattr(json_data, 'read'):
                # 文件对象
                json_bytes = json_data.read()
            else:
                # 直接字节流
                json_bytes = json_data

            # 保存到临时文件或直接处理
            with BytesIO(json_bytes) as temp_file:
                data = nh_ai.upload_scheme_from_price_query(
                    json_file_path=temp_file,
                    order_no=order_no,
                    byte=True
                )

        return data

    @staticmethod
    def formatting_diy_price_data(file_data) -> list:
        """
        提取Excel数据并转换为指定格式，支持文件路径、字节流或文件对象

        Args:
            file_data: 可以是文件路径(str/pathlib.Path)、字节流(bytes/BytesIO)或文件对象
        """
        # 根据输入类型读取Excel文件
        if isinstance(file_data, (str, Path)):
            # 文件路径方式
            df = pd.read_excel(file_data, sheet_name='Sheet1')
        elif isinstance(file_data, (bytes, BytesIO)):
            # 字节流方式
            if isinstance(file_data, BytesIO):
                excel_bytes = file_data
            else:
                excel_bytes = BytesIO(file_data)
            df = pd.read_excel(excel_bytes, sheet_name='Sheet1')
        else:
            # 文件对象方式
            df = pd.read_excel(file_data, sheet_name='Sheet1')

        # 映射关系：Excel列名 -> 目标字段名
        column_mapping = {
            '报价编码': 'prodNum',
            '物料名称': 'prodName',
            '物料类型': 'quoteType',
            '产品类型': 'prodType',  # 注意：Excel中没有这个字段，设为空
            '长': 'length',
            '宽': 'width',
            '高': 'height',
            '面积': 'area',
            '数量': 'number',
            '单位': 'unit',
            '花色': 'color',
            '规格': 'spec',
            '备注': 'comments'
        }

        extracted_data = []

        for _, row in df.iterrows():
            # 跳过表头行（如果第一行是标题）
            if '序号' in row and row['序号'] == '序号':
                continue

            item = {}

            for chinese_col, english_key in column_mapping.items():
                if chinese_col in row:
                    # 处理数值类型字段
                    if english_key in ['length', 'width', 'height', 'area', 'number']:
                        value = row[chinese_col]
                        # 尝试转换为数值，如果失败则保持原样
                        try:
                            if pd.notna(value) and value != '':
                                # 处理浮点数，如果是整数则转换为int
                                float_val = float(value)
                                item[english_key] = int(float_val) if float_val.is_integer() else float_val
                            else:
                                item[english_key] = ''
                        except (ValueError, TypeError):
                            item[english_key] = value
                    else:
                        item[english_key] = row[chinese_col] if pd.notna(row[chinese_col]) else ''
                else:
                    # 如果Excel中没有该列，设为空值
                    item[english_key] = ''

            # 特殊处理：Excel中没有'产品类型'字段，设为空
            item['prodType'] = ''

            extracted_data.append(item)

        return extracted_data

    def get_product_price(self, price_data):
        """提取产品价格信息"""
        price_items = {
            "prodNum": "报价编码", "prodName": "物料名称", "quoteType": "物料类型",
            "prodType": "产品类型", "length": "长", "width": "宽", "height": "高",
            "area": "面积", "number": "数量", "unit": "单位", "color": "花色",
            "spec": "规格", "comments": "备注"
        }

        # 使用字典推导式，添加默认值处理
        return {
            english_key: price_data.get(english_key, '')
            for english_key, chinese_name in price_items.items()
        }

    def extract_scheme_prices(self, data) -> list:
        """提取方案价格列表"""
        scheme_prices = []

        # 使用安全的数据访问方式
        space_list = data.get("data", {}).get("spaceList", []) if data else []

        for space in space_list:
            for group in space.get("groupList", []):
                # 直接遍历 productTree，如果不存在则使用空列表
                for product in group.get("productTree", []):
                    scheme_prices.append(self.get_product_price(product))

        return scheme_prices


if __name__ == '__main__':
    pass
    from tools.src.order_comparator import OrderComparator
    json_file = r"D:\缓存用\Download\WXWork\1688850695996741\Cache\File\2025-09\1758099483730.json"
    order_no = "L02490125000040"
    tcp = TocProductPrice(host="dev")
    # 使用方式保持不变
    data = tcp.get_nh_ai_price_data(json_file, order_no)
    print(data)
    scheme_prices1 = tcp.extract_scheme_prices(data)
    print(f"提取到 {len(scheme_prices1)} 个产品价格信息")
    excel = r"D:\缓存用\Download\WXWork\1688850695996741\Cache\File\2025-09\-定制家具-报价表.xls"
    scheme_prices2 = tcp.formatting_diy_price_data(excel)
    comparator = OrderComparator(
        scheme_prices2,
        scheme_prices1,
        key_field="prodNum",
        name_field="prodName",
        exclude_fields=[
            "prodNum",
            "prodName",
            "quoteType",
            "prodType",
            "length",
            "width",
            "height",
            "area",
            "number",
            "unit",
            "color",
            "spec",
            "comments"
        ]
    )
    print(comparator.compare_json_data())
