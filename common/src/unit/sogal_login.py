# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：sogal_login
@Time ：2025/7/8 15:46
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""

import logging

import requests
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LdapUtils:
    @staticmethod
    def get_connection(url, login_suffix, account_name, credentials):
        """
        建立 LDAP 连接
        :param url: LDAP 服务器地址
        :param login_suffix: 账号后缀
        :param account_name: 用户名
        :param credentials: 密码
        :return: LDAP 连接对象
        """
        try:
            # 创建服务器对象
            server = Server(f'ldap://{url}', get_info=ALL)

            # 拼接完整用户名
            user_dn = f"{account_name}{login_suffix if login_suffix else ''}"

            # 建立连接并绑定
            conn = Connection(
                server,
                user=user_dn,
                password=credentials,
                auto_bind=True
            )
            return conn
        except LDAPBindError:
            raise RuntimeError("账号或者密码错误")
        except LDAPException as e:
            raise RuntimeError(f"LDAP连接错误: {str(e)}")

    @staticmethod
    async def get_user(umas_properties, user_name, password) -> dict:
        """
        获取用户信息
        :param umas_properties: 配置对象
        :param user_name: 用户名
        :param password: 密码
        :return: 用户属性字典
        """
        return LdapUtils.execute(
            lambda conn: LdapUtils._get_user(conn, umas_properties, user_name),
            umas_properties,
            user_name,
            password
        )

    @staticmethod
    def _get_user(conn, umas_properties, user_name):
        """
        在已建立的连接上查询用户信息
        :param conn: LDAP 连接
        :param umas_properties: 配置对象
        :param user_name: 用户名
        :return: 用户属性字典
        """
        user_map = {}
        base_dn = umas_properties.oa['base']
        account_attr = umas_properties.oa['account_attribute']

        try:
            # 构造搜索过滤器
            search_filter = f"({account_attr}={user_name})"

            # 执行搜索
            conn.search(
                search_base=base_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['*']  # 获取所有属性
            )

            # 处理搜索结果
            for entry in conn.entries:
                for attr in entry.entry_attributes:
                    # 处理多值属性
                    values = entry[attr].values
                    if len(values) == 1:
                        user_map[attr] = str(values[0])
                    else:
                        user_map[attr] = [str(v) for v in values]

            # 调试日志
            if logger.isEnabledFor(logging.DEBUG):
                for key, value in user_map.items():
                    logger.debug(f"k={key}, v={value}")

            return user_map
        except LDAPException as e:
            raise RuntimeError(f"获取用户信息错误: {str(e)}")

    @staticmethod
    def execute(func, umas_properties, user_name, password):
        """
        执行 LDAP 操作并确保连接关闭
        :param func: 要执行的函数
        :param umas_properties: 配置对象
        :param user_name: 用户名
        :param password: 密码
        :return: 函数执行结果
        """
        conn = None
        try:
            oa_config = umas_properties.oa
            conn = LdapUtils.get_connection(
                oa_config['url'],
                oa_config.get('login_suffix', ''),
                user_name,
                password
            )
            return func(conn)
        finally:
            if conn:
                conn.unbind()


# 示例配置对象结构
class UmasProperties:
    # 初始化UmasProperties类
    def __init__(self):
        # 定义oa字典，包含url、base、login_suffix和account_attribute四个键值对
        self.oa = {
            'url': '10.10.10.10:389',  # LDAP服务器地址
            'base': 'DC=sogal,DC=org',  # LDAP服务器基本DN
            'login_suffix': '@sogal.org',  # 登录后缀
            'account_attribute': 'sAMAccountName'  # 账户属性
        }

def format_phone_smart(phone):
    phone = str(phone).strip()
    if not phone.isdigit():
        raise ValueError("必须为数字")

    # 已有1开头则直接补0，否则添加1再补0
    if phone.startswith('1'):
        return phone.ljust(11, '0')
    else:
        return ('1' + phone).ljust(11, '0')
# 使用示例
if __name__ == "__main__":
    # try:
    #     # 创建配置对象
    #     umas_props = UmasProperties()
    #     # 获取用户信息
    #     user_info = LdapUtils.get_user(umas_props, "11031840", "hubangguo199780")
    #     print("用户信息:", user_info)
    #
    #     # 获取特定属性
    #     email = user_info.get('mail', '')
    #     name = user_info.get('displayName', '')
    #     print("用户邮箱:", email)
    #     print("用户姓名:", name)
    #
    # except Exception as e:
    #     print("操作失败:", str(e))

    print(format_phone_smart('011'))