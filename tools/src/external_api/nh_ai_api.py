# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：nh_ai_api
@Time ：2025/9/16 9:23
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
import os
import sys
import time
import base64
import requests
from Crypto.PublicKey import RSA
from typing import Optional, Dict
from Crypto.Cipher import PKCS1_v1_5
from common.settings import NHAI_CONFIG
from datetime import datetime, timedelta
from tools.src.external_api.cookie_manager import CookieManager
from requests_toolbelt.multipart.encoder import MultipartEncoder

# 添加项目路径
AUTOTESTPROJECT_PATH = os.path.realpath(os.path.dirname(os.path.abspath(__file__)) + '/../../')
sys.path.append(AUTOTESTPROJECT_PATH)

# 通过调试从前端源码中获取到的公钥
public_key = ("MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzk48wcG3r3KMF14kH6KV"
              "+5dIU1f7aJyZxfhSiXLPLGJvY9LcXra68NJuyWpQMKF5MYRwoDMl87PuCEwQuSiiXbUMW2F7ky33C8A8OZvHhpETdnlTOnShd1VI7"
              "/nZ4Lg5l/w11+S3BkTzEh65tpiTQ+mflhPGrzrxL2sRYew6joXpSXjOQMVH4xR4fQIMaq/SChVvs"
              "/dYABwtsp9p6gmXcGRH6Iypmp8Qz9m3k6kxHp5eEyYLUTGLwInVfjHVndBNx1mP73PVM7nC4M7DUKT2ysOAqQL"
              "+MH3AxpLjYikBiFi3VGjJUcb3Itfb+kUB2XMJ2VJs7c2w1LzA3R/XIymUXQIDAQAB")


class NeuroHomeApi:
    _host = {
        'test': 'https://api-test.neurohome-ai.com',  # NHAI测试环境地址
        'dev': 'https://api-dev.neurohome-ai.com',  # NHAI开发环境地址
        'data': 'https://api-data.neurohome-ai.com',  # NHAI数据环境地址
        # 'm': 'https://api-test.neurohome-ai.com'  # NHAI木门测试环境地址
    }
    # OSS地址映射
    _oss_host = {
        'test': 'https://nhai-static-test.oss-cn-hangzhou.aliyuncs.com',
        'dev': 'https://nhai-static-dev.oss-cn-hangzhou.aliyuncs.com',
        'data': 'https://nhai-static-data.oss-cn-hangzhou.aliyuncs.com'
    }

    def __init__(self, host="test",
                 username=NHAI_CONFIG.get("default_user"),
                 password=NHAI_CONFIG.get("default_password")):

        self.username = username
        self.password = password
        self.session = requests.session()
        if host not in self._host.keys():
            raise Exception("host参数错误")
        self.host = self._host.get(host)
        self.oss_host = self._oss_host.get(host, f'https://nhai-static-{host}.oss-cn-hangzhou.aliyuncs.com')
        self.env = host
        # 初始化Cookie管理器
        self.cookie_manager = CookieManager(service_name="nh_ai")
        self._load_cookies()

        # 如果cookies无效则重新登录
        if not self._check_cookies_valid():
            self.login()

    def _load_cookies(self):
        """加载cookies到session"""
        cookies = self.cookie_manager.load_cookies("nh_ai", self.username)
        if cookies:
            self.session.cookies.update(cookies)

    def _save_cookies(self):
        """保存当前session的cookies"""
        self.cookie_manager.save_cookies(
            env_name=self.env,
            username=self.username,
            base_url=self.host,
            cookies=self.session.cookies
        )

    def _check_cookies_valid(self) -> bool:
        """
        检查当前cookies是否有效
        :return: True表示有效，False表示无效
        """
        try:
            # 尝试访问一个需要认证的接口来检查cookies有效性
            url = f"{self.host}/api/umas/user/front/current"
            response = self.session.get(url, verify=False, timeout=5)
            if "账号未登录" in response.text:
                return False
            return response.status_code == 200 and "data" in response.json()
        except Exception:
            return False

    # 生成加密后的密码
    def get_encrypted_password(self):
        public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
        rsa_key = RSA.import_key(public_key_pem)
        cipher = PKCS1_v1_5.new(rsa_key)

        encrypted = cipher.encrypt(self.password.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    def login(self):
        """登录并保存cookies"""
        url = f"{self.host}/api/public/oauth2/token"
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.get_encrypted_password(),
            "client_id": "manage-client",
            "client_secret": "manage-client"
        }

        # 清除旧的cookies
        self.session.cookies.clear()

        r = self.session.post(url, data=data, verify=False)
        response_data = r.json()

        # 保存cookies
        self._save_cookies()

        return response_data

    def clear_cookies(self):
        """清除当前用户的cookies缓存"""
        self.cookie_manager.clear_cookies(self.env, self.username)
        print(f"已清除nh_ai环境{self.username}用户的Cookie缓存")

    def _request_with_cookie_check(self, method, url, **kwargs):
        """
        统一的请求方法，自动检查cookies是否有效
        :param method: 请求方法
        :param url: 请求URL
        :param kwargs: 其他请求参数
        """
        try:
            response = self.session.request(method, url, **kwargs)

            # 检查是否因为cookies过期导致请求失败
            if response.status_code == 401 or "token" in response.text.lower() or "账号未登录" in response.text:
                print("检测到cookies可能已过期，尝试重新登录...")
                # 重新登录获取新的cookies
                self.login()
                # 使用新的cookies重试请求
                response = self.session.request(method, url, **kwargs)

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败: {str(e)}")

    def _get(self, url, **kwargs):
        """GET请求封装"""
        return self._request_with_cookie_check('GET', url, **kwargs)

    def _post(self, url, **kwargs):
        """POST请求封装"""
        return self._request_with_cookie_check('POST', url, **kwargs)

    def get_user_info(self):
        """
        获取登录用户信息(门店信息、组织信息等)
        """
        url = f"{self.host}/api/umas/user/front/current"
        r = self._get(url, verify=False)
        return r.json()

    def get_kjl_account(self):
        """
        获取登录用户的酷家乐账号信息
        """
        url = f"{self.host}/api/umas/thirdparty/account/user/current"
        r = self._get(url, verify=False)
        return r.json()

    def query_sj(self, bg_time=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00"),
                 ed_time=datetime.now().strftime("%Y-%m-%d 23:59:59"),
                 query_type="有效客户",
                 user_id=None,
                 ):
        """
        查询商机方案
        """
        url = f"{self.host}/api/thirdpartyapi/open/xplan/sjQuery"
        if not user_id:
            user_id = self.get_user_info().get("data").get("thirdId")
        data = {"page": 1,
                "beginTime": bg_time,
                "endTime": ed_time,
                "limit": 10,
                "timeType": "createCus",
                "queryType": query_type,
                "userId": user_id
                }
        r = self._post(url, json=data, verify=False)
        return r.json()

    def query_brand_opty(self, opty_id=None, user_id=None):
        """
        获取商机方案信息页，第一个商机方案的信息
        """
        url = f"{self.host}/api/thirdpartyapi/open/xplan/optyBrandQuery"
        if not opty_id:
            opty_id = self.query_sj().get("data")[0].get("optyId")
        if not user_id:
            user_id = self.get_user_info().get("data").get("thirdId")
        data = {"optyId": opty_id,
                "page": 1,
                "userId": user_id
                }
        r = self._post(url, json=data, verify=False)
        return r.json()

    def get_scheme_info(self, opty_id=None):
        """
        获取方案信息
        """
        url = f"{self.host}/api/scheme/scheme-manage/page-scheme"
        if not opty_id:
            opty_id = self.query_sj().get("data")[0].get("optyId")
        data = {"businessId": opty_id,
                "schemeType": 1,
                "pageNo": 1,
                "pageSize": 10,
                "sortList": [{"field": "modifyTime", "type": "DESC"}]
                }
        r = self._post(url, json=data, verify=False)
        return r.json()

    def get_projection_equivalent(self, opty_id):
        """
        获取方案安装折合方数信息
        """
        url = f"{self.host}/api/order-analyzer/orderAnalyzerData/install"

        data = {
            "orderNo": str(opty_id),
            "productId": "",
            "productName": "",
            "area": "",
            "areaType": 2,
            "pageNo": 1,
            "pageSize": 1000
        }
        r = self._post(url, json=data, verify=False)
        return r.json()

    def get_projection_equivalent_area(self, opty_id):
        """
        获取方案安装折合方数面积信息
        """
        url = f"{self.host}/api/order-analyzer/orderAnalyzerData/install-area"
        data = {
            "orderNo": str(opty_id),
            "productId": "",
            "productName": "",
            "area": "",
            "areaType": 2,
            "pageNo": 1,
            "pageSize": 1000
        }
        r = self._post(url, json=data, verify=False)
        return r.json().get("data", 0)

    def get_projection_install(self, opty_id):
        """
        获取方案投影安装方数信息
        """
        url = f"{self.host}/api/order-analyzer/orderAnalyzerData/install"
        data = {
            "orderNo": str(opty_id),
            "productId": "",
            "productName": "",
            "area": "",
            "areaType": 1,
            "pageNo": 1,
            "pageSize": 1000
        }
        r = self._post(url, json=data, verify=False)
        return r.json()

    def get_projection_install_area(self, opty_id):
        """
        获取方案投影安装面积信息
        """
        url = f"{self.host}/api/order-analyzer/orderAnalyzerData/install-area"
        data = {
            "orderNo": str(opty_id),
            "productId": "",
            "productName": "",
            "area": "",
            "areaType": 1,
            "pageNo": 1,
            "pageSize": 1000
        }
        r = self._post(url, json=data, verify=False)
        return r.json().get("data", 0)

    def get_order_mark_query(self, opty_id, code=''):
        """
        获取方案订单标识查询信息
        """
        url = f"{self.host}/api/order-analyzer/orderAnalyzerData/order-sign"
        if code is None:
            code = ''
        data = {
            "orderNo": str(opty_id),
            "signCode": str(code),
            "signName": "",
            "signType": "",
            "signValue": "",
            "pageNo": 1,
            "pageSize": 1000
        }
        r = self._post(url, json=data, verify=False)
        return r.json()

    def get_queue_management(self, opty_id):
        """
        获取任务队列管理信息
        """
        url = f"{self.host}/api/order-task/orderTask/backend/task/list"
        data = {
            "orderNo": str(opty_id),
            "factoryNo": "",
            "customerNo": "",
            "taskState": "",
            "orderCategory": "",
            "orderType": "",
            "orderBrand": "",
            "orderPlace": "",
            "errorText": "",
            "modifyTime": [],
            "pageNo": 1,
            "pageSize": 1000
        }
        r = self._post(url, json=data, verify=False)
        return r.json()

    def get_quotation_detail(self, order_no="", quotation_code="", quotation_name="", quotation_type=""):
        """
        获取报价数据
        :pama
        order_no: 订单号
        quotation_code: 报价编码
        quotation_name: 报价名称
        quotation_type: 报价类型（1.清单报价，2.投影报价，3.新渠道报价，4.橱柜报价。不填则所有）
        """
        url = f"{self.host}/api/order-analyzer/orderAnalyzerData/quotation"
        data = {"orderNo": order_no,
                "quotationCode": quotation_code,
                "quotationName": quotation_name,
                "quotationType": quotation_type,
                "pageNo": 1,
                "pageSize": 200
                }
        r = self._post(url, json=data, verify=False)
        return r.json()

    def get_relation_order(self, order_no):
        """获取关联订单信息"""
        url = f"{self.host}/api/order-analyzer/orderAnalyzer/relationOrder?orderNo={order_no}"
        r = self._get(url, verify=False)
        return r.json()

    def get_batch_form_sign(self, keys: list, protocol_type: int = 0) -> Optional[Dict]:
        """
        获取批量表单签名
        :param keys: 需要签名的文件名列表
        :param protocol_type: 协议类型，0为默认，1为阿里云，2为腾讯云
        :return: 签名信息
        """
        url = f"{self.host}/api/cloudstorage/batch-form-sign"
        data = {
            "protocolType": protocol_type,
            "keys": keys
        }

        try:
            response = self._post(url, json=data)
            return response.json()
        except Exception as e:
            print(f"获取表单签名失败: {e}")
            return None

    def upload_to_oss(self, file_data: Dict, file_content: bytes, filename: str) -> bool:
        """
        上传文件到OSS（使用MultipartEncoder优化）
        :param file_data: 文件数据
        :param file_content: 文件内容
        :param filename: 文件名
        :return: 上传是否成功
        """
        sign_params = file_data.get('signParams', {})
        if not sign_params:
            print("错误: 未找到signParams字段")
            return False
        # 准备表单字段
        fields = {
            'OSSAccessKeyId': sign_params['OSSAccessKeyId'],
            'policy': sign_params['policy'],
            'signature': sign_params['signature'],
            'success_action_status': sign_params.get('success_action_status', '200'),
            'x-oss-meta-auth': sign_params.get('x-oss-meta-auth', ''),
            'key': file_data['key'],  # 这个字段在顶层
            'file': (filename, file_content, 'application/json')
        }

        # 添加所有非文件字段
        multipart_data = MultipartEncoder(
            fields=fields,
            boundary='----WebKitFormBoundary' + ''.join([str(i) for i in range(10)])
        )

        headers = {
            "Content-Type": multipart_data.content_type,
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"24\", \"Chromium\";v=\"116\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "referrer": f"https://work-{self.env}.neurohome-ai.com/",
        }

        try:
            # 使用独立的session上传到OSS（不携带cookies）
            oss_session = requests.Session()
            response = oss_session.post(
                self.oss_host,
                headers=headers,
                data=multipart_data,
                timeout=30
            )
            print(f"OSS上传响应状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"OSS上传响应内容: {response.text}")

            response.raise_for_status()
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"上传到OSS失败: {e}")
            if 'response' in locals():
                print(f"响应内容: {response.text}")
            return False

    def create_task(self, task_data: Dict) -> Optional[Dict]:
        """
        创建分析任务
        :param task_data: 任务数据
        :return: 任务创建结果或None
        """
        url = f"{self.host}/api/order-analyzer/orderAnalyzer/createTask"

        try:
            response = self._post(url, json=task_data)
            return response.json()
        except Exception as e:
            print(f"创建任务失败: {e}")
            return None

    def price_json_transform(self, oss_key):
        """
        场景文件加工（dhc数据加工）
        """
        url = f'{self.host}/scheme/scheme-manage/ctrl-transform-url'
        try:
            response = self._post(url, json={"osskey": oss_key})
            return response.json()
        except Exception as e:
            print(f"创建任务失败: {e}")
            return None

    def get_price_data_for_oss(self, oss_key):
        """
        获取价格数据
        """
        url = f'{self.host}/quotation/quotation/getConsumerQuotationAutoTest'
        try:
            response = self._post(url, json={"schemeOssKey": oss_key})
            return response.json()
        except Exception as e:
            print(f"创建任务失败: {e}")
            return None


class NeuroHomeApiOss(NeuroHomeApi):
    def __init__(self, host="test", username=NHAI_CONFIG.get("default_user"),
                 password=NHAI_CONFIG.get("default_password")):
        super().__init__(host, username, password)

    def upload_scheme_files_and_create_task(self, scheme_json_content: bytes, scheme_info_content: bytes,
                                            order_no: str) -> Optional[Dict]:
        """
        完整的上传流程：上传方案文件和信息文件，然后创建任务
        :param scheme_json_content: 方案JSON文件内容
        :param scheme_info_content: 方案信息文件内容
        :param order_no: 订单号
        """
        # 获取订单信息
        order_info_result = self.get_relation_order(order_no)
        order_info = order_info_result.get('data')
        if order_info:
            factory_no = order_info.get('factoryNo')
            dealer_no = order_info.get('dealerNo')
            customer_no = order_info.get('customerNo')
            task_type = order_info.get('taskType')
        else:
            print("获取订单信息失败")
            return None

        # 生成时间戳和文件路径
        timestamp = str(int(time.time() * 1000))
        scheme_json_key = f"public/temp/scheme/design/{order_no}_{timestamp}/{timestamp}.json"
        scheme_info_key = f"public/temp/scheme/design/{order_no}_{timestamp}/{timestamp}_infor.json"

        print(f"开始上传文件，订单号: {order_no}")
        print(f"方案JSON路径: {scheme_json_key}")
        print(f"方案信息路径: {scheme_info_key}")
        print(f"工厂号: {factory_no}")
        # 1. 获取两个文件的签名
        sign_response = self.get_batch_form_sign([scheme_json_key, scheme_info_key])
        if not sign_response or 'data' not in sign_response:
            print("获取文件签名失败")
            print(f"响应: {sign_response}")
            return None
        print(f"签名响应: {sign_response}")
        print("获取文件签名成功")

        # 2. 上传方案JSON文件
        json_file_data = next((item for item in sign_response['data'] if item['key'] == scheme_json_key), None)
        if not json_file_data:
            print("未找到方案JSON文件的签名数据")
            print(f"可用keys: {[item['key'] for item in sign_response['data']]}")
            return None

        print("开始上传方案JSON文件...")
        if not self.upload_to_oss(json_file_data, scheme_json_content, f"{timestamp}.json"):
            print("上传方案JSON文件失败")
            return None

        print("上传方案JSON文件成功")

        # 3. 上传方案信息文件
        info_file_data = next((item for item in sign_response['data'] if item['key'] == scheme_info_key), None)
        if not info_file_data:
            print("未找到方案信息文件的签名数据")
            return None

        print("开始上传方案信息文件...")
        if not self.upload_to_oss(info_file_data, scheme_info_content, f"{timestamp}_infor.json"):
            print("上传方案信息文件失败")
            return None

        print("上传方案信息文件成功")

        # 4. 创建任务
        task_data = {
            "orderNo": order_no,
            "factoryNo": factory_no,
            "dealerNo": dealer_no,
            "customerNo": customer_no,
            "schemeJsonPath": scheme_json_key,
            "schemeInfoPath": scheme_info_key,
            "taskType": task_type
        }

        print("开始创建任务...")
        result = self.create_task(task_data)

        if result:
            print("任务创建成功")
            print(f"任务响应: {result}")
        else:
            print("任务创建失败")

        return result

    def upload_scheme_from_task_queue(self, json_file_path: str, info_file_path: str, order_no: str) -> Optional[Dict]:
        """
        从文件路径上传方案文件并创建任务
        :param json_file_path: 方案JSON文件路径
        :param info_file_path: 方案信息文件路径
        :param order_no: 订单号
        :return: 任务创建结果或None
        """
        try:
            # 读取文件内容
            with open(json_file_path, 'rb') as f:
                scheme_json_content = f.read()

            with open(info_file_path, 'rb') as f:
                scheme_info_content = f.read()

            return self.upload_scheme_files_and_create_task(
                scheme_json_content, scheme_info_content, order_no)
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None

    def upload_scheme_files_and_create_price(self, scheme_json_content: bytes, order_no: str) -> Optional[Dict]:
        """
        完整的上传流程：上传方案文件和信息文件，然后创建任务
        :param scheme_json_content: 方案JSON文件内容
        :param order_no: 订单号
        """

        # 生成时间戳和文件路径
        timestamp = str(int(time.time() * 1000))
        scheme_json_key = f"public/temp/{order_no}_{timestamp}.json"

        print(f"开始上传文件，订单号: {order_no}")
        print(f"方案JSON路径: {scheme_json_key}")

        # 1. 获取两个文件的签名
        sign_response = self.get_batch_form_sign([scheme_json_key])

        if not sign_response or 'data' not in sign_response:
            print("获取文件签名失败")
            print(f"响应: {sign_response}")
            return None
        print(f"签名响应: {sign_response}")
        print("获取文件签名成功")

        # 2. 上传方案JSON文件
        json_file_data = next((item for item in sign_response['data'] if item['key'] == scheme_json_key), None)
        if not json_file_data:
            print("未找到方案JSON文件的签名数据")
            print(f"可用keys: {[item['key'] for item in sign_response['data']]}")
            return None

        print("开始上传方案JSON文件...")
        if not self.upload_to_oss(json_file_data, scheme_json_content, f"{timestamp}.json"):
            print("上传方案JSON文件失败")
            return None

        print("上传方案JSON文件成功")

        # 3. 报价json加工
        price_transform = self.price_json_transform(scheme_json_key)
        print(price_transform)
        # return result
        # 4. 获取报价数据
        if "data" in price_transform:
            return self.get_price_data_for_oss(price_transform["data"].get("ossPath"))
        else:
            print("获取报价失败")
            return None

    def upload_scheme_from_price_query(self, json_file_path: str, order_no: str, byte=False) -> Optional[Dict]:
        try:
            if not byte:
                # 读取文件内容
                with open(json_file_path, 'rb') as f:
                    scheme_json_content = f.read()
            else:
                scheme_json_content = json_file_path

            return self.upload_scheme_files_and_create_price(scheme_json_content, order_no)
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None


if __name__ == '__main__':
    nhapi = NeuroHomeApiOss(host='test')
    # print(nhapi.get_user_info())
    # print(nhapi.get_kjl_account())
    # print(nhapi.query_sj())
    # print(nhapi.query_brand_opty())
    oid = 'L0040012500680-52'
    print("投影安装方数信息", nhapi.get_projection_install(oid))
    print("投影安装方数面积信息", nhapi.get_projection_install_area(oid))
    print("安装折合方数信息", nhapi.get_projection_equivalent(oid))
    print("安装折合方数面积信息", nhapi.get_projection_equivalent_area(oid))
    # print("订单标识查询信息", nhapi.get_order_mark_query(oid))
    # print("方案报价数据查询", nhapi.get_quotation_detail(oid))
    # print("任务队列管理信息", nhapi.get_queue_management(oid))

    # print(nhapi.get_relation_order('L0040012500655-81'))
    # print(nhapi.upload_scheme_from_task_queue(
    #     json_file_path=r"D:\缓存用\Download\WXWork\1688850695996741\Cache\File\2025-09\1758099483730.json",
    #     info_file_path=r"D:\缓存用\Download\WXWork\1688850695996741\Cache\File\2025-09\1758099478662_infor.json",
    #     order_no="L0249012500004-30"
    # ))
    # print(nhapi.upload_scheme_from_price_query(
    #     json_file_path=r"D:\缓存用\Download\WXWork\1688850695996741\Cache\File\2025-09\1758099483730.json",
    #     order_no="L02490125000040"
    # ))
    import json

    # print(json.dumps(nhapi.get_price_data_for_oss("public/temp/scheme/design/ctrlX/1758588502310.json"), indent=4, ensure_ascii=False))
