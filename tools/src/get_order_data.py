# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：get_order_data
@Time ：2025/9/15 8:20
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from collections import defaultdict

from typing import Union, List, Dict
import json
from suds.client import Client
import pandas as pd


def col_in_df(df):
    if 'EdgeBanding' not in df.columns:
        df['EdgeBanding'] = None
    if 'Color' not in df.columns:
        df['Color'] = None
    if 'Remark' not in df.columns:
        df['Remark'] = None


class GetOrderData:
    _host = {'t': 'http://192.168.2.197',  # 测试环境的计料系统数据获取
             'f': 'http://mrp.sogal.net',  # 工厂正式环境
             'g': 'http://192.168.2.197',  # 工厂正式环境
             }

    def __init__(self, host='t', filter_column: Union[list, tuple] = None):
        self.host = self._host.get(host)
        if self.host:
            try:
                self.url = f'{self.host}/ERPStatus/MCSWebService.asmx?wsdl'
                self.client = Client(self.url)
                self.filter_column = filter_column
            except Exception as e:
                print(f'连接ERP系统失败，请检查网络连接，错误信息：{e}')
        else:
            print('host定义错误')

        self.temporary_data_list = list()

    def filter_order_column(self, data: dict, stock_up_type=None):
        if self.filter_column is None:
            return data
        if "StockUpType" in self.filter_column and stock_up_type is not None:
            if data.get('StockUpType') in [None, '']:
                data['StockUpType'] = stock_up_type
        return {key: data.get(key, '') for key in self.filter_column}

    def result_analyse(self, original_data):
        # print(original_data)
        for _data_value in original_data['LstOGD']:
            """
            判断解析数据是否有LstOPD子节点数据，因为有LstOPD子项数据需要提取LstOPD子项数据才是最终数据依赖
            """
            if len(_data_value.get('LstOPD')) == 1:
                # 物料数据类型字段补充提取
                if _data_value['StockUpType'] not in ["1", "3", 1, 3, '', None]:  # 板件五金排除
                    self.temporary_data_list.append(self.filter_order_column(_data_value))  # 单独添加外层的
                self.temporary_data_list.append(
                    self.filter_order_column(_data_value.get('LstOPD')[0], _data_value['StockUpType']))
            elif len(_data_value.get('LstOPD')) > 1:
                # 以防意外记录是否有异常差异数据，测试用
                if _data_value['StockUpType'] not in ["1", "3", 1, 3, '', None]:  # 板件五金排除
                    self.temporary_data_list.append(self.filter_order_column(_data_value))  # 单独添加外层的
                for _data_value_subset in _data_value.get('LstOPD'):
                    self.temporary_data_list.append(
                        self.filter_order_column(_data_value_subset, _data_value['StockUpType']))
            else:
                # 其他LstOPD为空的数据直接引用原数据
                self.temporary_data_list.append(self.filter_order_column(_data_value))
        return self.temporary_data_list

    def result_data_integration(self, out_StockUpType=False):
        df_store = pd.DataFrame(self.temporary_data_list)
        col_in_df(df_store)
        if out_StockUpType:
            df_store = df_store[  # 数据提取
                ['StockUpType', 'Code', 'Name', 'Color', 'Height', 'Width', 'Length', 'Quantity', 'Remark',
                 'EdgeBanding']
            ]
            # 重命名列名称并排序
            df_store.columns = ['物料类型', '物料编码', '名称', '花色', '高', '成品宽', '成品长', '数量', '备注',
                                '封边']
            df_sorted = df_store.sort_values(by=['物料类型', '物料编码'], ascending=[True, True])
            return df_sorted
        else:
            df_store = df_store[['Name', 'Color', 'Height', 'Width', 'Length', 'Quantity', 'Remark', 'EdgeBanding']]
            df_store.columns = ['名称', '花色', '高', '成品宽', '成品长', '数量', '备注', '封边']
            df_store = df_store.sort_values(by=['高', '成品宽', '成品长', '名称', '花色', '数量', '备注', '封边'])
            return df_store


def get_data_for_only(host='t', order_no=None, filter_column=None):
    """
    单个订单数据提取
    :param host: 计料系统host
    :param order_no: 订单号
    :param filter_column: 需要对比的字段列表
    """
    params_dict = {"auth": "mcsuser", "orderNoJsonP": str([f'{order_no}'])}
    order_client = GetOrderData(host=host, filter_column=filter_column)
    _result = order_client.client.service.GetMcsOrderDataByOrderNo(**params_dict)
    result = json.loads(_result)
    if result[0].get("Result") not in ["false", False, 0, None, "null"]:
        excel_name = result[0].get('OrderNo')
        return {excel_name: order_client.result_analyse(result[0])}


def get_data_for_batch(host='t', order_nos: list = None, filter_column=None):
    """
    批量订单数据提取
    :param host: 计料系统host
    :param order_nos: 订单号列表
    :param filter_column: 需要对比的字段列表
    """
    params_dict = {"auth": "mcsuser", "orderNoJsonP": str(list(order_nos))}
    order_client = GetOrderData(host=host, filter_column=filter_column)
    result = order_client.client.service.GetMcsOrderDataByOrderNo(**params_dict)
    order_result = {}
    for order in json.loads(result):
        if order.get("Result") not in ["false", False, 0, None, "null"]:
            excel_name = order.get('OrderNo')
            order_result[excel_name] = order_client.result_analyse(order)
    return order_result


if __name__ == '__main__':
    pass
    # params_dict = {"auth": "mcsuser", "orderNoJsonP": str(['Y116805125000005-4207', 'Y116805125000005-4206'])}
    comparison_column = ['StockUpType', 'Code', 'Name', 'Color', 'Height', 'Width', 'Length', 'Quantity', 'Remark',
                         'EdgeBanding']
    # Orderclient = GetOrderData(host='t', filter_column=comparison_column)
    # result = Orderclient.client.service.GetMcsOrderDataByOrderNo(**params_dict)
    # print(result)
    # for h in json.loads(result):
    #     excel_name = h.get('OrderNo')
    #     # try:
    #     print(Orderclient.result_analyse(h))
    #     # df = Orderclient.result_data_integration(out_StockUpType=True)
    #     # print(df)
    #     # if not os.path.exists(data_save_path):
    #     #     os.makedirs(data_save_path)
    #     # except Exception as e:
    #     #     print(e)
    # print(get_data_for_batch(host='t', order_nos=['L04700125000003-949'],
    #                          filter_column=None))
    from tools.src.order_comparator import OrderComparator

    new_info = get_data_for_only('t', "L0040012500529-153", comparison_column)
    old_info = get_data_for_only('t', "L0040012500529-152", comparison_column)
    print(old_info.get("L0040012500529-152"))
    print(new_info.get("L0040012500529-153"))
    oc = OrderComparator(old_info.get("L0040012500529-152"), new_info.get("L0040012500529-153"))
    print(oc.compare_json_data())
    a = [{'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 543.5,
          'Length': 565.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'},
         {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 531.5,
          'Length': 865.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'},
         {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 543.5,
          'Length': 865.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'}]
    b = [
        {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 531.5,
         'Length': 865.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'},
        {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 543.5,
         'Length': 865.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'},
        {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 543.5,
         'Length': 565.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'},
    ]
    print(OrderComparator(a, b).compare_json_data())
    #      'stats': {'total_differences': 0, 'only_in_list1': 0, 'only_in_list2': 0, 'count_differences': 0,
    #                    'content_differences': 0, 'total_rows': 3}
    {'comparison': [{'key': 'F10A1-1', 'name': '非标上固层', 'stockType': 1, 'status': 'identical',
                     'data1': {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG',
                               'Height': 18.0, 'Width': 531.5, 'Length': 865.0, 'Quantity': 1.0, 'Remark': '',
                               'EdgeBanding': '四○'},
                     'data2': {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG',
                               'Height': 18.0, 'Width': 531.5, 'Length': 865.0, 'Quantity': 1.0, 'Remark': '',
                               'EdgeBanding': '四○'}, 'differences': {}},
                    {'key': 'F10A1-1', 'name': '非标上固层', 'stockType': 1, 'status': 'identical',
                     'data1': {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG',
                               'Height': 18.0, 'Width': 543.5, 'Length': 565.0, 'Quantity': 1.0, 'Remark': '',
                               'EdgeBanding': '四○'},
                     'data2': {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG',
                               'Height': 18.0, 'Width': 543.5, 'Length': 565.0, 'Quantity': 1.0, 'Remark': '',
                               'EdgeBanding': '四○'}, 'differences': {}},
                    {'key': 'F10A1-1', 'name': '非标上固层', 'stockType': 1, 'status': 'identical',
                     'data1': {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG',
                               'Height': 18.0, 'Width': 543.5, 'Length': 865.0, 'Quantity': 1.0, 'Remark': '',
                               'EdgeBanding': '四○'},
                     'data2': {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG',
                               'Height': 18.0, 'Width': 543.5, 'Length': 865.0, 'Quantity': 1.0, 'Remark': '',
                               'EdgeBanding': '四○'}, 'differences': {}}],
     'stats': {'total_differences': 0, 'only_in_list1': 0, 'only_in_list2': 0, 'count_differences': 0,
               'content_differences': 0, 'total_rows': 3}}

