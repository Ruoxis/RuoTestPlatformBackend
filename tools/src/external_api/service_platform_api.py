# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：service_platform_api
@Time ：2025/9/16 9:24
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe：综合服务平台API封装类，使用CookieManager管理cookies
"""
import json
import os.path
import re
import sys
import zipfile
from ast import literal_eval
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import requests
from dateutil.parser import parse
from requests_toolbelt.multipart.encoder import MultipartEncoder

AUTOTESTPROJECT_PATH = os.path.realpath(os.path.dirname(os.path.abspath(__file__)) + '/../../')
sys.path.append(AUTOTESTPROJECT_PATH)
from common.settings import SERVICE_PLATFORM_CONFIG, BASE_DIR
from tools.src.external_api.cookie_manager import CookieManager


class ServicePlatformAPI:
    """综合服务平台API封装类"""

    # 状态字典
    STATUS_DICT = {
        "1": "新任务", "2": "重新执行任务", "3": "完成任务", "4": "人工处理", "5": "完成解析Jx文件",
        "6": "完成检查图纸数据", "7": "完成解析订单标识", "8": "完成解析Xml数据", "9": "完成解析趟门数据",
        "10": "完成解析报价数据", "11": "完成提交营销协同系统信息", "12": "完成提交营销协同系统预报价",
        "13": "完成提交计料系统信息", "14": "完成上传Xml", "15": "完成炸单", "16": "完成导入计料数据",
        "17": "完成校验订单", "18": "人工处理", "101": "更新状态中", "102": "解析Jx文件中",
        "103": "检查图纸数据中", "104": "解析订单标识中", "105": "解析Xml数据中", "106": "解析趟门数据中",
        "107": "解析报价数据中", "108": "提交营销协同系统信息中", "109": "提交营销协同系统预报价中",
        "110": "提交计料系统信息中", "111": "上传Xml中", "112": "炸单中", "113": "导入计料数据中",
        "114": "校验订单中", "115": "人工处理标识提交中", "1001": "更新状态失败", "1002": "下载文件失败",
        "1003": "解析Jx文件失败", "1004": "检查图纸数据失败", "1005": "解析订单标识失败",
        "1006": "解析Xml数据失败", "1007": "解析趟门数据失败", "1008": "解析报价数据失败",
        "1009": "提交营销协同系统信息失败", "1010": "提交营销协同系统预报价失败",
        "1011": "提交计料系统信息失败", "1012": "上传Xml失败", "1013": "炸单失败",
        "1014": "导入计料数据失败", "1015": "校验订单失败", "1016": "人工处理标识提交失败"
    }

    # 请求头
    DEFAULT_HEADERS = {
        "X-Requested-With": "XMLHttpRequest",
        "X-FineUIMvc-Ajax": "true",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    _host = {
        't': 'http://10.10.18.107:8090/',  # 综合服务平台地址
        'f': 'http://diyhome.sfygroup.com/',  # 经销商服务平台地址
        'p': 'http://10.10.18.110:8090/',  # PRE环境综合服务平台地址
        'm': 'http://10.10.18.205:8080/'  # 木门综合服务平台地址
    }
    _env = {
        't': 'test',  # 综合服务平台地址
        'f': 'formal',  # 经销商服务平台地址
        'p': 'pre',  # PRE环境综合服务平台地址
        'm': 'mum'  # 木门综合服务平台地址
    }

    def __init__(self, host: str = 't', username: str = SERVICE_PLATFORM_CONFIG.get("username"),
                 password: str = SERVICE_PLATFORM_CONFIG.get("password")):
        """
        初始化API客户端
        :param host: 综合服务平台地址标识
        :param username: 用户名
        :param password: 密码
        :param env_name: 环境名称，用于cookie缓存
        """
        self.username = username
        self.password = password

        if host not in self._host.keys():
            raise Exception("host参数错误")
        self.base_url = self._host.get(host)
        self.env_name = self._env.get(host)
        # 初始化Cookie管理器
        self.cookie_manager = CookieManager(service_name="service_platform", cache_dir=None)

        # 尝试加载缓存的cookies，如果不存在或过期则重新登录
        self.cookies = self._cookies_valid()
        print(f"初始化完成，base_url: {self.base_url}")

    def _get_cookies(self) -> requests.cookies.RequestsCookieJar:
        """获取cookies，优先使用缓存，如果不存在或过期则重新登录"""
        # 尝试从缓存加载cookies
        cached_cookies = self.cookie_manager.load_cookies(self.env_name, self.username)
        if cached_cookies:
            print("使用缓存的cookies")
            return cached_cookies

        # 缓存中没有或已过期，重新登录
        print("重新登录获取cookies")
        return self._login_and_save_cookies()

    def _login_and_save_cookies(self) -> requests.cookies.RequestsCookieJar:
        """登录并保存cookies"""
        cookies = self._login()
        # 保存cookies到缓存，默认24小时过期
        self.cookie_manager.save_cookies(
            env_name=self.env_name,
            username=self.username,
            base_url=self.base_url,
            cookies=cookies
        )
        return cookies

    def _login(self) -> requests.cookies.RequestsCookieJar:
        """登录获取cookies"""
        try:
            data = {
                "account": self.username,
                "password": self.password,
                "returnUrl": ""
            }
            response = requests.post(
                f'{self.base_url}/Account/Login',
                headers=self.DEFAULT_HEADERS,
                data=data
            )
            response.raise_for_status()
            return response.cookies
        except Exception as err:
            raise Exception(f"登录失败: {str(err)}")

    def _request_with_cookie_check(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        统一的请求方法，自动检查cookies是否有效
        :param method: 请求方法，如'POST'、'GET'等
        :param url: 请求URL
        :param kwargs: 其他请求参数
        """
        # 设置默认headers
        headers = kwargs.pop('headers', {})
        final_headers = {**self.DEFAULT_HEADERS, **headers}
        if not self.cookies:
            self.cookies = self._cookies_valid()
        # 设置cookies
        kwargs['cookies'] = self.cookies
        try:
            response = requests.request(method, url, headers=final_headers, **kwargs)

            # 检查是否因为cookies过期导致请求失败
            if "登录超时" in response.text:
                print("检测到cookies可能已过期，尝试重新登录...")
                # 清除旧的cookies缓存
                self.cookie_manager.clear_cookies(self.env_name, self.username)
                # 重新登录获取新的cookies
                self.cookies = self._login_and_save_cookies()
                # 使用新的cookies重试请求
                kwargs['cookies'] = self.cookies
                response = requests.request(method, url, headers=final_headers, **kwargs)

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败: {str(e)}")

    def _post(self, url: str, **kwargs) -> requests.Response:
        """POST请求封装"""
        return self._request_with_cookie_check('POST', url, **kwargs)

    def _get(self, url: str, **kwargs) -> requests.Response:
        """GET请求封装"""
        return self._request_with_cookie_check('GET', url, **kwargs)

    def check_cookies_valid(self) -> bool:
        """
        检查当前cookies是否有效
        :return: True表示有效，False表示无效
        """
        try:
            # 尝试一个简单的请求来检查cookies有效性
            return self._cookies_valid()
        except Exception as err:
            print(err)
            return False

    def _cookies_valid(self):
        cookies = self._get_cookies()
        data = {
            "txtOrderNoKey": "order_no",
            "txtFactoryNoKey": "",
            "ddlTaskStatusSearchKey": "",
            "ddlOrderTypeSearchKey": "",
            "gridTaskQueue_pagingToolbar_pageNumberBox": "1",
            "ddlPageSize": "1000",
            "gridTaskQueue_fields": '["OrderNo","TaskStatus","Message","LastUpdatedBy","LastUpdatedTime","Id"]',
            "gridTaskQueue_pageIndex": "0",
            "gridTaskQueue_pageSize": "1000",
            "ddlTaskStatusSearchKey_text": "",
            "ddlOrderTypeSearchKey_text": "",
            "ddlPageSize_text": "1000",
            "__RequestVerificationToken": "wVyeehAA-XLoFD9pDf3-ISOzJozO4B3b_c44PBdwDvF1fGSFrmd4HuI8sb_k2tYhNrHGdyZN52bM-u90o97KuDtuO_M_ZHIDGBpzZC37J7s1",
        }
        try:
            # 尝试一个简单的请求来检查cookies有效性
            response = requests.post(f'{self.base_url}Task/TaskQueue/Search', cookies=cookies,
                                     data=data, headers=self.DEFAULT_HEADERS)
            if "登录超时" in response.text:
                return False
            else:
                return cookies
        except Exception as err:
            print(err)
            return False

    def get_status(self, order_no: str) -> Dict[str, str]:
        """
        获取订单炸单状态
        :param order_no: 订单编号
        """
        data = {
            "txtOrderNoKey": order_no,
            "txtFactoryNoKey": "",
            "ddlTaskStatusSearchKey": "",
            "ddlOrderTypeSearchKey": "",
            "gridTaskQueue_pagingToolbar_pageNumberBox": "1",
            "ddlPageSize": "1000",
            "gridTaskQueue_fields": '["OrderNo","TaskStatus","Message","LastUpdatedBy","LastUpdatedTime","Id"]',
            "gridTaskQueue_pageIndex": "0",
            "gridTaskQueue_pageSize": "1000",
            "ddlTaskStatusSearchKey_text": "",
            "ddlOrderTypeSearchKey_text": "",
            "ddlPageSize_text": "1000",
            "__RequestVerificationToken": "wVyeehAA-XLoFD9pDf3-ISOzJozO4B3b_c44PBdwDvF1fGSFrmd4HuI8sb_k2tYhNrHGdyZN52bM-u90o97KuDtuO_M_ZHIDGBpzZC37J7s1",
        }

        response = self._post(
            f'{self.base_url}/Task/TaskQueue/Search',
            data=data
        )

        pattern = r'\[.*\]'
        regex = re.compile(pattern)
        results = regex.findall(response.text)
        print(response.text)
        if not results:
            raise Exception("未找到状态信息")

        result_parts = results[0].split(",")

        return {
            "TaskStatus": self.STATUS_DICT.get(result_parts[1], "未知状态"),
            "Message": result_parts[2][1:-1],
            "LastUpdatedTime": result_parts[4][1:-3].replace("T", " ").replace("Z", " "),
            "rowIndexs": result_parts[5].replace("]", " ")
        }

    def get_projection_area(self, order_no: str, code: str = '') -> List[Dict[Any, Any]] | None:
        """
        散单投影安装方数查询
        :param order_no: 订单编号
        :param code: 模块编码
        :return: 包含尺寸和面积信息的字典列表
        """
        data = {
            "txtOrderNoKey": order_no,
            "txtCodeKey": code,
            "txtNameKey": "",
            "txtAreaKey": "",
            "gridAreaInstall_pagingToolbar_pageNumberBox": "1",
            "ddlPageSize": "1000",
            "gridAreaInstall_fields": '["Id","Code","OrderNo","OrderTimestamp","ObjId","Name","Width","Depth","Height","Area","CreatedDateTime"]',
            "gridAreaInstall_pageIndex": "0",
            "gridAreaInstall_pageSize": "1000",
            "ddlPageSize_text": "1000",
            "__RequestVerificationToken": "bV3QgrVviaUzPQBBZSN7JjQOLKT9NdlaPbkvDwuvYtq0muuTvb9whZ3_hsZxfaWPDOuQLhHUETmmbABIlkTshGFg9jBZ7_8yMMbr7WS5UcE1",
        }

        response = self._post(
            f'{self.base_url}/DiyHomeData/AreaInstallDetail/Search',
            data=data
        )

        pattern = r'\[\[.*\]\]'
        regex = re.compile(pattern)
        results = regex.findall(response.text)

        if not results:
            return None

        new_list = literal_eval(results[0])
        result_data = []
        for i in new_list:
            result_data.append(dict(zip(["id", "Code", "orderNo", "OrderTimestamp", "ObjId", "productName",
                                         "width", "depth", "height", "area", "CreatedDateTime"], i)))

        return result_data

    # 其他方法也按照同样的方式修改，使用 self._post 和 self._get 替代原始的 requests调用
    # 这里只展示部分方法的修改，其他方法需要类似修改

    def get_convert_area(self, order_no: str, code: str = '') -> List[Dict[Any, Any]] | None:
        """散单安装折合方式查询"""
        data = {
            "txtOrderNoKey": order_no,
            "txtCodeKey": code,
            "txtNameKey": "",
            "txtAreaKey": "",
            "txtEqAreaKey": "",
            "gridAreaConvert_pagingToolbar_pageNumberBox": "1",
            "ddlPageSize": "1000",
            "gridAreaConvert_fields": '["Id", "Code", "OrderNo", "OrderTimestamp", "ObjId", "Name", "Width", "Depth", "Height", "Area", "EQArea", "CreatedDateTime"]',
            "gridAreaConvert_pageIndex": "0",
            "gridAreaConvert_pageSize": "1000",
            "ddlPageSize_text": "1000",
            "__RequestVerificationToken": "GrGm6w1130i2oAc88BTT4aKfD7S6m58NCGs6-teL6nqS-c3UuS3WG2PbrwEDHwzTxfW0krihOVMLjdwQKfJ8HCvHd8YtYDdtn0N4HHcKeoU1",
        }

        response = self._post(
            f'{self.base_url}/DiyHomeData/AreaConvertDetail/Search',
            data=data
        )

        pattern = r'\[\[.*\]\]'
        regex = re.compile(pattern)
        results = regex.findall(response.text)
        if not results:
            return None

        new_list = literal_eval(results[0])
        result_data = []
        for i in new_list:
            result_data.append(dict(
                zip(["id", "Code", "orderNo", "OrderTimestamp", "ObjId", "productName", "width", "depth", "height",
                     "area", "EQArea", "CreatedDateTime"], i)))
        return result_data

    def get_cabinet_install_data(self, order_no: str, code: str = "") -> List[Dict[Any, Any]] | None:
        """获取橱柜安装数据"""
        data = {
            "txtOrderNoKey": order_no,
            "txtMaterialCodeKey": code,
            "ddlStructureCategoryKey": "",
            "gridCabinetInstall_pagingToolbar_pageNumberBox": "1",
            "ddlPageSize": "1000",
            "gridCabinetInstall_fields": '["Id","Code","OrderNo","OrderTimestamp","MaterialNumber","MaterialCode","MaterialName","Color","Width","Depth","Height","Structure","StructureCategory","Unit","QuantityMeter","Coefficient","CreatedDateTime"]',
            "gridCabinetInstall_pageIndex": "0",
            "gridCabinetInstall_pageSize": "1000",
            "ddlStructureCategoryKey_text": "",
            "ddlPageSize_text": "1000",
            "__RequestVerificationToken": "ld-AcvMflGpe6b7-_IfZaVfVDLQv-VdvcY75OFNLj4ZPoWpXMXbuSBULDhp_jlZZ-KFBcH8VX1mj4Eh0TL95dcewKu0x-tjx0D0jvNstNv01",
        }

        response = self._post(
            f'{self.base_url}/DiyHomeData/CabinetInstallDetail/Search',
            data=data
        )

        pattern = r'\[\[.*\]\]'
        regex = re.compile(pattern)
        results = regex.findall(response.text)
        if not results:
            return None

        new_list = literal_eval(results[0])
        result_data = []
        for i in new_list:
            result_data.append(dict(
                zip(["id", "Code", "orderNo", "OrderTimestamp", "ObjId", "productName", "width", "depth", "height",
                     "area", "EQArea", "CreatedDateTime"], i)))
        return result_data

    def operate_error_task(self, order_no: str) -> str:
        """操作错误任务"""
        data = {
            "orderNo": order_no,
            "errorOperationType": "4"
        }

        response = self._post(
            f'{self.base_url}/Task/TaskQueue/OperateErrorTask',
            data=data
        )
        return response.text

    def upload_jx(self, order_no: str, factory_no: str, jx_file_path: str) -> str:
        """上传JX文件"""
        fields = {
            "OrderNo": order_no,
            "FactoryNo": factory_no,
            "DealerNo": "jdtest07",
            "CustomerNo": "P02650",
            "X-FineUIMvc-Ajax": "true",
            "__RequestVerificationToken": "nFbTNOoLH21TuNoVTEyS9gWJNA6lksQnR3ck3kcYfBfqjgeqd_03IyXbQ3kl7Q6poYxM-i8CpoNbx6uAzfFW2csLKh2OoPSi8l0zmgAshcA1",
            "fuJxFile": (
                os.path.basename(jx_file_path),
                open(jx_file_path, 'rb'),
                'application/octet-stream'
            )
        }

        boundary = "----WebKitFormBoundaryCfVUcdAszfmEP7CG"
        m = MultipartEncoder(fields=fields, boundary=boundary)

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }

        response = self._post(
            f'{self.base_url}/Task/TaskQueueLog/SaveNewTask',
            headers=headers,
            data=m
        )
        return response.text

    def get_order_info(self, order_no: str) -> Dict:
        """获取订单信息"""
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
        }

        params = {"orderNo": order_no}

        response = self._get(
            f'{self.base_url}Task/TaskQueueLog/GetRelatedOrder',
            headers=headers,
            params=params
        )
        return json.loads(response.text)

    def upload_jx_with_info(self, order_no: str, jx_file_path: str) -> str:
        """使用订单信息上传JX文件"""
        order_info = self.get_order_info(order_no)

        fields = {
            "OrderNo": order_no,
            "FactoryNo": order_info.get('FactoryNo'),
            "DealerNo": order_info.get('DealerNo'),
            "CustomerNo": order_info.get('CustomerNo'),
            "X-FineUIMvc-Ajax": "true",
            "__RequestVerificationToken": "WpZglOEN28UZgHBpN-R-lxM-lGiu2HQQKCNYZIKT0byucvHmucmjM6on1wZxC72hXoBHgyk8NJnxfRnzqnaiXt4st54B5EiRYM7TU2i9veU1",
            "fuJxFile": (
                f"{order_no}.jx",
                open(jx_file_path, 'rb'),
                'application/octet-stream'
            )
        }

        boundary = "----WebKitFormBoundaryczSsfqcDFuvsMwyv"
        m = MultipartEncoder(fields=fields, boundary=boundary)

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }

        response = self._post(
            f'{self.base_url}/Task/TaskQueueLog/SaveNewTask',
            headers=headers,
            data=m
        )
        return response.text

    def download_xml(self, order_no: str, save_path: str) -> str:
        """下载XML文件"""

        def check_download_xml(order_no):
            """检查并获取下载XML所需参数"""
            data = {"orderNo": order_no}
            response = self._post(
                f'{self.base_url}/Task/TaskQueue/CheckDownloadXml',
                data=data
            )
            return response.text

        try:
            xml_content = check_download_xml(order_no)
            factory_no = re.findall(r'Basket=&quot;(.*)&quot;&gt', xml_content)[0]

            data = {
                "FactoryNo": factory_no,
                "xmlContent": xml_content
            }

            response = self._post(
                f'{self.base_url}/Task/TaskQueue/DownloadXml',
                data=data
            )

            save_file = os.path.join(save_path, f"{order_no}.xml")
            with open(save_file, 'w', encoding='utf-8') as f:
                f.write(response.text.replace('\n', ''))

            return save_file
        except Exception as e:
            raise Exception(f"下载XML失败: {str(e)}")

    def get_drawing_tag_value(self, order_no: str, tag_code: str = '', r_value=True) -> List[Dict[Any, Any]] | None:
        """获取图纸标识值"""
        if tag_code is None:
            tag_code = ''
        data = {
            "txtOrderNoKey": order_no,
            "txtTagCodeKey": str(tag_code),
            "ddlDrawingTagTypeKey": "",
            "gridDrawingTagDetail_pagingToolbar_pageNumberBox": 1,
            "ddlPageSize": 1000,
            "gridDrawingTagDetail_fields": '["Id","OrderNo","OrderTimestamp","TagCode","TagName","TagValue","TagType","IsCrmUsed","IsMrpUsed","CreatedDateTime"]',
            "gridDrawingTagDetail_pageIndex": "0",
            "gridDrawingTagDetail_pageSize": "1000",
            "ddlDrawingTagTypeKey_text": "",
            "ddlPageSize_text": 1000,
            "__RequestVerificationToken": "cYjRYhh4dxV64A1Is_UySOrfJWqjwrR_F7898LzMZd2IOcXL6bguTUiwrHhGY_3o5XY5LfhjeepsPRtE79MEYlHbaBKznpeZ8OPHSOoBvSI1",
        }

        response = self._post(
            f'{self.base_url}/DiyHomeData/DrawingTagDetail/Search',
            data=data
        )

        response_text = response.text

        # 查找 loadData( 后面的数据
        start_index = response_text.find('loadData(')
        if start_index == -1:
            return None
        start_index += len('loadData(')
        end_index = response_text.find(');', start_index)
        if end_index == -1:
            return None
        data_str = response_text[start_index:end_index]
        try:
            data_str = data_str.replace('true', 'True').replace('false', 'False')
            new_list = eval(data_str)
        except Exception as e:
            print(f"解析数据失败: {e}")
            return None
        result_data = []
        for i in new_list:
            result_data.append(dict(
                zip(["id", "orderNo", "OrderTimestamp", "signCode", "TagName", "signValue", "signType", "IsCrmUsed",
                     "status", "CreatedDateTime"], i)))
        if r_value and result_data:
            return result_data[0].get("signValue")
        else:
            return result_data

    def get_quotation_detail_value(self, order_no: str, code_key: str = '', r_value=False) -> List[Dict[
        Any, Any]] | None:
        """获取报价单明细"""
        if code_key is None:
            code_key = ''
        data = {
            "txtOrderNoKey": order_no,
            "txtCodeKey": str(code_key),
            "ddlQuotationTypeKey": "",
            "cbxIsSelectBackupsKey": "false",
            "gridQuotationDetail_pagingToolbar_pageNumberBox": 0,
            "ddlPageSize": '1000',
            "gridQuotationDetail_fields": '["Id","OrderNo","OrderTimestamp_Str","MaterialType","Code","Name","ObjName","StrObjId","StrBaseParentId","Length","Width","Thickness","SeriesType","Quantity","Spec","Area","ColorCode","ColorName","Unit","UnitPrice","DepthRate","PriceRate","BodyNo","LinearMeterRate","PriceFlag","Discount","Amount","ProductNum","StandProperty","StandRatio","SynthesisRatio","Remark","ObjIds","QuoteCatVersion","QuotationType","CreatedDateTime"]',
            "gridQuotationDetail_pageIndex": "0",
            "gridQuotationDetail_pageSize": "1000",
            "ddlQuotationTypeKey_text": "",
            "ddlPageSize_text": '1000',
            "__RequestVerificationToken": "22KFJ_COdac82_K9qiLdDpm-JiPQXZukLi1DNfMfDcHmpH6j4HTNsN6Ce-8dIzPU0xQC9ab75ipEUkb6_FwZ5rSrmjyvQjf58eMPKoZywsQ1",
        }

        response = self._post(
            f'{self.base_url}/DiyHomeData/QuotationDetail/Search',
            data=data
        )

        response_text = response.text

        # 查找 loadData( 后面的数据
        start_index = response_text.find('loadData(')
        if start_index == -1:
            return None
        start_index += len('loadData(')
        end_index = response_text.find(');', start_index)
        if end_index == -1:
            return None
        data_str = response_text[start_index:end_index]
        try:
            data_str = data_str.replace('true', 'True').replace('false', 'False')
            new_list = eval(data_str)
        except Exception as e:
            print(f"解析数据失败: {e}")
            return None
        result_data = []
        for i in new_list:
            result_data.append(dict(
                zip(["id", "orderNo", "orderTimestamp_Str", "materialType", "code", "name", "objName", "strObjId",
                     "strBaseParentId", "length", "width", "thickness", "seriesType", "quantity", "speac", "area",
                     "colorCode", "colorName", "unit", "unitPrice", "depthRate", "priceRate", "bodyNo",
                     "linearMeterRate", "priceFlag", "discount", "amount", "productNum", "standProperty", "standRatio",
                     "synthesisRatio", "remark", "objIds", "quoteCatVersion", "quotationType", "createdDateTime"], i)))
        if r_value and result_data:
            return result_data[0].get("signValue")
        else:
            return result_data

    def redo_all_steps(self, order_no: str) -> str:
        """重新执行所有炸单步骤"""
        try:
            row_index = self.get_status(order_no).get("rowIndexs")
            data = {
                "operateType": "4",
                "rowIndexs[]": row_index,
            }

            response = self._post(
                f'{self.base_url}/Task/TaskQueue/BatchOperateOrder',
                data=data
            )

            pattern = r'\[.*\]'
            regex = re.compile(pattern)
            results = regex.findall(response.text)

            if results:
                message = json.loads(results[0])[0].get('Message', '')
                return f"{order_no}: {message}"
            else:
                return f"{order_no}: 重新执行成功"

        except Exception as e:
            return f"{order_no}: 重新执行失败 - {str(e)}"

    def batch_push_order_pre(self, order_numbers: str) -> str:
        """批量推送订单到预发布环境"""
        data = {
            "orderNos": order_numbers,
            "__RequestVerificationToken": "TJuUh3MxieylW2iUoFjRA4rDAHa-7wtkh5nKXAsP_pJ3cE7NHtU0rc2zIN0zbFmpcQRELTCWzwX4lm5drCnl-5QzAmTJg_-z2SbfD7INK1A1"
        }

        response = self._post(
            f'{self.base_url}/Task/TaskQueueLog/BatchPushOrderPre',
            data=data
        )
        return response.text

    def download_jx(self, order_no: str, save_path: str) -> str:
        """下载JX文件"""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{self.base_url}/Task/TaskQueue/BatchDownload",
            "Priority": "u=4",
            "Upgrade-Insecure-Requests": "1"
        }

        data = {
            "downloadType": '0',
            "orderNosJson": str([order_no])
        }

        response = self._post(
            f'{self.base_url}/Task/TaskQueue/BatchDownloadFile',
            headers=headers,
            data=data
        )

        zip_path = os.path.join(save_path, f'{order_no}.zip')
        with open(zip_path, 'wb') as zipf:
            zipf.write(response.content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(zip_path))

        os.remove(zip_path)
        return os.path.dirname(zip_path)

    def clear_cookies(self):
        """清除当前用户的cookies缓存"""
        self.cookie_manager.clear_cookies(self.env_name, self.username)
        print(f"已清除{self.env_name}环境{self.username}用户的Cookie缓存")
    def get_obj_detail_data(self, order_no='', code=''):
        """
        获取场景数据
        :param order_no: 订单编号
        :param code: 模块编码
        :return:
        """
        data = {
            "txtOrderNoKey": order_no,
            "txtObjCodeKey": code,
            "txtProductTagKey": "",
            "cbxIsSelectBackupsKey": "false",
            "gridObjectDetail_pagingToolbar_pageNumberBox": "1",
            "ddlPageSize": "500",
            "gridObjectDetail_fields": '["Id","OrderNo","OrderTimestamp","StrObjId","StrParentId","StrBaseParentId","SecondId","ObjType","ObjCode","ObjName","Width","Depth","Height","PosX","PosY","PosZ","Degree","ColorCode","ObjCodeFlag","ProductTag","ObjCustomParams","WallId","LeftWallId","RightWallId","FrontWallId","BackWallId","SecondWallIds","CreatedDateTime"]',
            "gridObjectDetail_pageIndex": "0",
            "gridObjectDetail_pageSize": "50",
            "ddlPageSize_text": "50",
            "__RequestVerificationToken": "cH7t6Jk5h15JIpMXvnFYN55DSzfnhNXJF_Z_1DVht_qi5HL2aoKt5ATFrYihLiynU4HRHN74K0GMngII-0lX_ykfN-ruaPZ-djYZm70_Cb01",
        }

        response = self._post(
            f'{self.base_url}/DiyHomeData/ObjectDetail/Search',
            data=data
        )

        pattern = r'\[\[.*\]\]'
        regex = re.compile(pattern)
        results = regex.findall(response.text)

        if not results:
            return None

        new_list = literal_eval(results[0])
        result_data = []
        for i in new_list:
            result_data.append(dict(
                zip(["Id", "OrderNo", "OrderTimestamp", "StrObjId", "StrParentId", "StrBaseParentId", "SecondId",
                     "ObjType", "ObjCode", "ObjName", "Width", "Depth", "Height", "PosX", "PosY", "PosZ", "Degree",
                     "ColorCode", "ObjCodeFlag", "ProductTag", "ObjCustomParams", "WallId", "LeftWallId", "RightWallId",
                     "FrontWallId", "BackWallId", "SecondWallIds", "CreatedDateTime"], i)))

        return result_data

    def obj_sift_order(self, code, start_day, start_time, sift_cause="建议NH项目筛单", order_bg_day="2025-03-01",
                       order_bg_time="00:00", order_ed_day="2025-09-01", order_ed_time="00:00"):
        """
        通过code筛单
        :param code: 物体编码
        :param start_day: 开始执行筛单日期
        :param start_time: 开始执行筛单时间
        :param sift_cause: 筛单原因
        :param order_bg_day: 订单开始日期
        :param order_bg_time: 订单开始时间
        :param order_ed_day: 订单结束日期
        :param order_ed_time: 订单结束时间
        后四个参数主要是确定筛单时间区间
        """
        data = {
            "Id": 0,
            "SiftCause": sift_cause,
            "BeginDate": order_bg_day,
            "BeginTime": order_bg_time,
            "EndDate": order_ed_day,
            "EndTime": order_ed_time,
            "ToMailIdList": "34",
            "JxType": "DPC_DHMD_PRODUCT_CABINET_MLN",
            "ddlParamName2": "",
            "CustomerNos": "",
            "SiftStartDate": start_day,
            "SiftStartTime": start_time,
            "txtParamCode1": "",
            "ddlCalculateType1": 0,
            "txtParamValue1": code,
            "txtParamCode2": "",
            "ddlCalculateType2": 0,
            "txtParamValue2": "",
            "gridObjectSiftDetail_fields": '["Id", "ParamName1", "ParamCode1", "SqlMethod1", "ParamValue1", "ParamName2","ParamCode2", "SqlMethod2", "ParamValue2", "IsFixed"]',
            "gridObjectSiftDetail_modifiedData": str(
                [{"index": 0, "values": {"ParamValue1": code}, "status": "modified", "originalIndex": 0,
                  "id": "-101"}]),
            "BeginTime_text": order_bg_time,
            "BeginTime_isUserInput": "false",
            "EndTime_text": order_ed_time,
            "EndTime_isUserInput": "false",
            "ToMailIdList_text": "谢东明",
            "JxType_text": "DPC_DHMD_PRODUCT_CABINET_MLN",
            "ddlParamName2_text": "",
            "SiftStartTime_text": start_time,
            "SiftStartTime_isUserInput": "false",
            "ddlCalculateType1_text": "",
            "ddlCalculateType2_text": "",
            "__RequestVerificationToken": "MNrkNFW5wIotjxqkd2KinpARtKhHUBumhtJXQUbNxK0Nu0IcvDTSr-UWVR0pxIUrA7Ivr7zDVvsJP_e77QVSxYoj_dcTAzfRgytYgYZvSQs1"
        }
        self._post(f'{self.base_url}/OrderData/ObjectSiftOrder/Save', data=data)

    def get_sift_result(self, start_day="2025-09-19", end_day="2025-09-20"):
        """
        获取筛单结果
        :param start_day: 开始日期
        :param end_day: 结束日期
        """
        data = {
            "dpBeginDateKey": start_day,
            "dpEndDateKey": end_day,
            "gridObjectDetail_pagingToolbar_pageNumberBox": 1,
            "ddlPageSize": 500,
            "gridObjectDetail_fields": '["Id","FilePath","SiftCause","BeginDateTime","EndDateTime","ObjCode","LastUpdatedBy","LastUpdatedTime","SiftStatus","OrderCount"]',
            "gridObjectDetail_pageIndex": 0,
            "gridObjectDetail_pageSize": 50,
            "ddlPageSize_text": 50,
            "__RequestVerificationToken": "Cz0x1ytG3ugLfG9G5CQ3uJgSWlv96B7RKuYEcOxW-Ww8twlKIOiij0b_bpaHM91K9vgjdiINRniOdjWrr0V9IPohieKN-MjKoIkPq55Xov41"

        }
        response = self._post(f'{self.base_url}/OrderData/ObjectSiftOrder/Search', data=data)
        pattern = r'\[\[.*\]\]'
        regex = re.compile(pattern)
        results = regex.findall(response.text)

        if not results:
            return None

        new_list = literal_eval(results[0])
        result_data = []
        for i in new_list:
            result_data.append(dict(zip(["Id","FilePath","SiftCause","BeginDateTime","EndDateTime","ObjCode","LastUpdatedBy","LastUpdatedTime","SiftStatus","OrderCount"], i)))
        return result_data

class MumenServiceAPI:
    """木门服务平台API封装类"""

    def __init__(self, username: str, password: str, base_url: str, env_name: str = "default"):
        """
        初始化木门API客户端
        """
        self.username = username
        self.password = password
        self.base_url = base_url
        self.env_name = env_name
        self.token = self._login()

    def _login(self) -> str:
        """登录获取token"""
        headers = {
            "Authorization": "Basic d2ViYXBwOjEyMzQ1Ng==",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
        }

        params = {
            "username": self.username,
            "password": str(self.password).lower(),
            "client_id": "webapp",
            "client_secret": "123456",
            "grant_type": "password",
        }

        response = requests.post(
            url=f"{self.base_url}oauth/token",
            params=params,
            headers=headers
        )
        response.raise_for_status()

        return response.json().get('data').get('access_token')

    def get_json_url(self, order_no: str) -> str:
        """获取JSON文件URL"""
        headers = {
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
            "Sec-Fetch-Mode": "cors",
            "Authorization": f"bearer {self.token}"
        }

        params = {
            "orderNo": order_no,
            "type": "3"
        }

        response = requests.get(
            url=f"{self.base_url}mdcs/api/task/order/getFilePath",
            headers=headers,
            params=params
        )
        response.raise_for_status()

        return response.json().get('data')

    def download_json(self, order_no: str, save_path: str) -> None:
        """下载JSON文件"""
        try:
            json_url = self.get_json_url(order_no)
            response = requests.get(url=json_url)
            response.raise_for_status()

            with open(save_path, 'w', encoding='gbk') as f:
                json.dump(json.loads(response.content.decode('gbk')), f, ensure_ascii=False, indent=4)

        except Exception as e:
            with open(save_path, 'w', encoding='gbk') as f:
                f.write(f"{e},请确认单号是否正确，是否已完成炸单！！！")


if __name__ == '__main__':
    # 使用示例
    service_api = ServicePlatformAPI()
    if service_api:
        # 检查cookies是否有效

        print("Cookies有效")
        order_no = 'Y116805125000005-4244'
        # 获取订单状态
        status = service_api.get_status(order_no)
        print(f"订单状态: {status}")

        # 获取投影面积
        area = service_api.get_projection_area(order_no)
        area1 = service_api.get_convert_area(order_no)
        tag = service_api.get_drawing_tag_value(order_no=order_no, tag_code='ShadeArea')
        tag1 = service_api.get_drawing_tag_value(order_no=order_no, tag_code='ConvertArea')
        tag2 = service_api.get_drawing_tag_value(order_no=order_no, tag_code='AutoQuotationLevel')
        quotation = service_api.get_quotation_detail_value(order_no)
        print(f"投影面积: {area}")
        print(f"安装折合: {area1}")
        print(f"图纸标记: {tag}")
        print(f"图纸标记: {tag1}")
        print(f"图纸标记: {tag2}")
        print(f"报价明细: {quotation}")
    else:
        print("服务API初始化失败")
