# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：get_service_platform_data
@Time ：2025/9/16 15:32
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 获取服务平台数据的工具类
"""
from typing import Optional, Union
from tools.src.external_api.nh_ai_api import NeuroHomeApi
from tools.src.external_api.service_platform_api import ServicePlatformAPI


class ServicePlatformData:
    def __init__(self, host: str, opty_id: str, category_type: Optional[int] = None):
        """
        初始化服务平台数据获取类
        :param host: 环境标识，支持 ['test', 'dev', 'data', 't', 'f', 'p', 'm']
        :param opty_id: 订单id
        :param category_type: 产品类型，可选参数，默认为None

        :return: None
        """
        self.host = host
        self.opty_id = opty_id
        self.category_type = category_type
        self.service_platform = self._setup_service_platform(host)

    def _setup_service_platform(self, host: str) -> Union[NeuroHomeApi, ServicePlatformAPI, None]:
        """
        根据host初始化对应的服务平台实例
        :param host: 环境标识，支持 ['test', 'dev', 'data', 't', 'f', 'p', 'm']
        :return: 对应的服务平台实例
        """
        nh_hosts = ['test', 'dev', 'data']
        sp_hosts = ['t', 'f', 'p', 'm']

        if host in nh_hosts:
            return NeuroHomeApi(host)
        elif host in sp_hosts:
            return ServicePlatformAPI(host)
        else:
            raise ValueError(f"不支持的主机：{host}。支持的主机为: {nh_hosts + sp_hosts}")


class AreaData(ServicePlatformData):
    def __init__(self, host: str, opty_id: str, area: int, category_type: Optional[int] = None):
        """
        初始化订单安装区域数据获取类
        :param area: 方数类型，可选参数，默认为None
        """
        super().__init__(host, opty_id, category_type)
        self.area = area

    def get_order_install_area(self) -> Union[dict, None]:
        """
        获取订单安装区域数据
        :return: 订单安装区域数据
        """
        if not self.service_platform:
            return None

        try:
            if isinstance(self.service_platform, NeuroHomeApi):
                return self._handle_area_neurohome_api()
            elif isinstance(self.service_platform, ServicePlatformAPI):
                return self._handle_area_service_platform_api()
        except Exception as e:
            print(f"Error getting order install area: {e}")
            return None

    def _data_cleansing_neurohome_api(self, data: dict):
        """处理NeuroHomeApi的安装区域数据获取"""
        rows = data.get('data', {}).get('rows', [])
        fields = ['productUuid', 'productName', 'width', 'height', 'depth', 'area']

        if not rows:
            return []
        new_rows = []
        for row in rows:
            # 使用字典推导式，特殊处理productUuid字段
            cleaned_row = {
                'Code' if field == 'productUuid' else field: row.get(field)
                for field in fields
            }
            new_rows.append(cleaned_row)

        return new_rows

    def _data_cleansing_service_platform_api(self, data):
        """ 处理ServicePlatformAPI的安装区域数据获取 """
        pass
        if self.area == 1:
            fields = ['Code', 'productName', 'width', 'height', 'depth', 'area']
        else:
            fields = ['Code', 'productName', 'width', 'height', 'depth', 'EQArea']
        new_rows = []
        if data:
            for row in data:
                if float(row.get("area" if self.area == 1 else "EQArea")) <= 0:
                    continue
                cleaned_row = {'area' if field == 'EQArea' else field: row.get(field) for field in fields}
                new_rows.append(cleaned_row)
        return new_rows

    def _handle_area_neurohome_api(self) -> Union[int, float, list, dict, None]:
        """处理NeuroHomeApi的安装区域数据获取"""
        if self.area == 1:
            install_area = self.service_platform.get_projection_install_area(opty_id=self.opty_id)
            install = self._data_cleansing_neurohome_api(
                self.service_platform.get_projection_install(opty_id=self.opty_id))
            return {"install": install, "install_area": install_area}
        elif self.area == 2:
            install_area = self.service_platform.get_projection_equivalent_area(opty_id=self.opty_id)
            install = self._data_cleansing_neurohome_api(
                self.service_platform.get_projection_equivalent(opty_id=self.opty_id))
            return {"install": install, "install_area": install_area}
        else:
            raise ValueError(f"Unsupported area type: {self.area}")

    def _handle_area_service_platform_api(self) -> Union[int, float, list, dict, None]:
        """处理ServicePlatformAPI的安装区域数据获取"""
        if self.category_type is None:
            return 0

        if self.area == 1:  # 投影
            if self.category_type == 0:
                install = self._data_cleansing_service_platform_api(
                    self.service_platform.get_projection_area(order_no=self.opty_id))  # 衣柜投影
            elif self.category_type == 1:
                install = self._data_cleansing_service_platform_api(
                    self.service_platform.get_cabinet_install_data(order_no=self.opty_id))  # 橱柜
            else:
                install = []
            install_area = self.service_platform.get_drawing_tag_value(order_no=self.opty_id, tag_code='ShadeArea')
            return {"install": install, "install_area": install_area}
        elif self.area == 2:  # 折合
            if self.category_type == 0:
                install = self._data_cleansing_service_platform_api(
                    self.service_platform.get_convert_area(order_no=self.opty_id))  # 衣柜折合
            elif self.category_type == 1:
                install = self._data_cleansing_service_platform_api(
                    self.service_platform.get_cabinet_install_data(order_no=self.opty_id))
            else:
                install = []
            install_area = self.service_platform.get_drawing_tag_value(order_no=self.opty_id, tag_code='ConvertArea')
            return {"install": install, "install_area": install_area}
        else:
            raise ValueError(f"不支持的 area or category: area={self.area}, category={self.category_type}")


class TagData(ServicePlatformData):
    def __init__(self, host: str, opty_id: str, tage_name: str = '', category_type: Optional[int] = None):
        """
        标签数据获取
        :param host: 服务地址
        :param opty_id: 订单号
        :param tage_name: 标签名称，可选参数，默认为None
        :param category_type: 产品类型，可选参数，默认为None
        """
        super().__init__(host, opty_id, category_type)
        self.tage_name = tage_name

    def get_order_tag(self) -> Union[dict, list, None]:
        """
        获取订单标签数据
        """
        try:
            if not self.service_platform:
                return None
            if isinstance(self.service_platform, NeuroHomeApi):
                return self._handle_tag_neurohome_api()
            elif isinstance(self.service_platform, ServicePlatformAPI):
                return self._handle_tag_service_platform_api()
        except Exception as e:
            print(f"Error getting order install area: {e}")
            return None

    def _data_cleansing_neurohome_api(self, data: dict):
        """处理NeuroHomeApi的安装区域数据获取"""
        rows = data.get('data', {}).get('rows', [])
        fields = ['signCode', 'signType', 'signName', 'signValue']
        processed_data = []
        if rows:
            for row in rows:
                if row.get("signValue") in ['', None, 'null']:
                    continue
                cleaned_row = {}
                for field in fields:
                    value = row.get(field)
                    if field == 'signType' and value is not None:
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            # 转换失败时保持原值
                            pass
                    cleaned_row[field] = value
                processed_data.append(cleaned_row)
            return processed_data
        else:
            return processed_data

    def _data_cleansing_service_platform_api(self, data):
        """ 处理ServicePlatformAPI的安装区域数据获取 """
        pass
        fields = ['signCode', 'signType', 'TagName', 'signValue']
        processed_data = []
        if data:
            for row in data:
                if row.get("signValue") in ['', None, 'null']:
                    continue
                cleaned_row = {}
                for field in fields:
                    if field == 'TagName':
                        cleaned_row['signName'] = row.get(field)
                    else:
                        cleaned_row[field] = row.get(field)
                processed_data.append(cleaned_row)
        return processed_data

    def _handle_tag_neurohome_api(self) -> Union[int, float, list, dict, None]:
        """处理NeuroHomeApi的标签数据获取"""
        tage_data = self._data_cleansing_neurohome_api(
            self.service_platform.get_order_mark_query(opty_id=self.opty_id, code=self.tage_name))

        return tage_data

    def _handle_tag_service_platform_api(self) -> Union[int, float, list, dict, None]:
        """处理ServicePlatformAPI的标签数据获取"""
        tage_data = self._data_cleansing_service_platform_api(
            self.service_platform.get_drawing_tag_value(order_no=self.opty_id, tag_code=self.tage_name, r_value=False))
        return tage_data


class QuotationData(ServicePlatformData):
    def __init__(self, host: str, opty_id: str, code_key: str = '', category_type: Optional[int] = None,
                 filter_column: list = None):
        """
        标签数据获取
        :param host: 服务地址
        :param opty_id: 订单号
        :param code_key: 标签名称，可选参数，默认为None
        :param category_type: 产品类型，可选参数，默认为None
        :param filter_column: 过滤字段，可选参数，默认为None
        """
        super().__init__(host, opty_id, category_type)
        self.code_key = code_key
        if not filter_column:
            self.fields = ['materialType', 'code', 'name', 'length', 'width', 'thickness', 'quantity', 'speac', 'area',
                           'colorCode', 'colorName', 'unit', 'depthRate', 'priceRate', 'bodyNo', 'linearMeterRate',
                           'priceFlag', 'quotationType', 'remark']
        else:
            self.fields = filter_column

    def get_order_quotation(self) -> Union[dict, list, None]:
        """
        获取订单标签数据
        """

        try:
            pass
            if not self.service_platform:
                return None
            if isinstance(self.service_platform, NeuroHomeApi):
                return self._handle_quotation_neurohome_api()
            elif isinstance(self.service_platform, ServicePlatformAPI):
                return self._handle_quotation_service_platform_api()
        except Exception as e:
            print(f"Error getting order install area: {e}")
            return None

    def _data_cleansing_neurohome_api(self, data: dict):
        """处理NeuroHomeApi的安装区域数据获取"""
        rows = data.get('data', {}).get('rows', [])
        new_rows = []
        if rows:
            return [{field: row.get(field) for field in self.fields} for row in rows]
        return new_rows

    def _data_cleansing_service_platform_api(self, data):
        """ 处理ServicePlatformAPI的安装区域数据获取 """
        new_rows = []
        if data:
            return [{field: row.get(field) for field in self.fields} for row in data]
        return new_rows

    def _handle_quotation_neurohome_api(self) -> Union[int, float, list, dict, None]:
        """处理NeuroHomeApi的标签数据获取"""
        quotation_data = self._data_cleansing_neurohome_api(
            self.service_platform.get_quotation_detail(order_no=self.opty_id, quotation_code=self.code_key))
        return quotation_data

    def _handle_quotation_service_platform_api(self) -> Union[int, float, list, dict, None]:
        """处理ServicePlatformAPI的标签数据获取"""
        quotation_data = self._data_cleansing_service_platform_api(
            self.service_platform.get_quotation_detail_value(order_no=self.opty_id, code_key=self.code_key))
        return quotation_data


if __name__ == '__main__':
    # 示例用法
    from tools.src.order_comparator import OrderComparator

    # service_data = AreaData(
    #     host='test',
    #     area=1,
    #     opty_id='L0040012500580-64',
    #     category_type=0
    # )
    # result = service_data.get_order_install_area()

    old_service_data = AreaData(host='t',
                                area=2,
                                opty_id='L0040012500680-53',
                                category_type=0)
    new_service_data = AreaData(host='test',
                                area=2,
                                opty_id='L0040012500680-52',
                                category_type=0)
    old_result = old_service_data.get_order_install_area()
    new_result = new_service_data.get_order_install_area()
    print(old_result)
    print(new_result)
    # comparator = OrderComparator(old_result, new_result, key_field="code",
    #                              name_field="name")

    #
    # print("===========================")
    # old_service_data = QuotationData(host='t',
    #                                  code_key='',
    #                                  opty_id='L0040012300795-22',
    #                                  category_type=0)
    # new_service_data = QuotationData(host='test',
    #                                  code_key='',
    #                                  opty_id='L0040012500655-81',
    #                                  category_type=0)
    # old_result = old_service_data.get_order_quotation()
    # new_result = new_service_data.get_order_quotation()
    # print(old_result)
    # print(new_result)
    # comparator = OrderComparator(old_result, new_result, key_field="code",
    #                              name_field="name")
    # print(comparator.compare_json_data())

    # old_service_data = QuotationData(host='t',
    #                                  code_key='',
    #                                  opty_id='L0040012500529-153',
    #                                  category_type=0)
    # new_service_data = QuotationData(host='test',
    #                                  code_key='',
    #                                  opty_id='L0040012500529-152',
    #                                  category_type=0)
    # old_result = old_service_data.get_order_quotation()
    # new_result = new_service_data.get_order_quotation()
    # print(old_result)
    # print(new_result)
    # comparator = OrderComparator(old_result, new_result, key_field="code",
    #                              name_field="name")
    # print(comparator.compare_json_data())
