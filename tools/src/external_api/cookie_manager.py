# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：cookie_manager
@Time ：2025/9/16 14:19
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe：Cookie管理器，按服务名称/环境名称_用户名称组织cookie文件
"""
import json
import os.path
import re
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import requests

# 添加项目路径
AUTOTESTPROJECT_PATH = os.path.realpath(os.path.dirname(os.path.abspath(__file__)) + '/../../')
sys.path.append(AUTOTESTPROJECT_PATH)
from common.settings import BASE_DIR


class CookieManager:
    """Cookie管理类，负责cookie的存储和加载，过期检查由调用方自行处理"""

    def __init__(self, service_name: str, cache_dir: str = None):
        """
        初始化Cookie管理器
        :param service_name: 服务名称
        :param cache_dir: 缓存目录，默认为common/cookie_cache
        """
        if cache_dir is None:
            cache_dir = os.path.join(BASE_DIR, "common/cookie_cache")

        # 创建服务特定的缓存目录
        self.cache_dir = os.path.join(cache_dir, service_name)
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_cookie_file_path(self, env_name: str, username: str) -> str:
        """
        获取cookie文件路径
        :param env_name: 环境名称
        :param username: 用户名
        :return: cookie文件路径
        """
        # 清理文件名中的非法字符
        safe_env = re.sub(r'[\\/*?:"<>|]', "_", env_name)
        safe_user = re.sub(r'[\\/*?:"<>|]', "_", username)

        filename = f"{safe_env}_{safe_user}.json"
        return os.path.join(self.cache_dir, filename)

    def save_cookies(self, env_name: str, username: str, base_url: str,
                     cookies: requests.cookies.RequestsCookieJar,
                     expire_time: datetime = None) -> str:
        """
        保存cookies到文件
        :param env_name: 环境名称
        :param username: 用户名
        :param base_url: 基础URL
        :param cookies: cookies对象
        :param expire_time: 过期时间，默认24小时
        """
        cookie_file = self.get_cookie_file_path(env_name, username)

        # 转换cookies为可序列化的字典
        cookie_dict = {}
        for name, value in cookies.items():
            cookie_dict[name] = value

        # 设置过期时间（默认24小时）
        if expire_time is None:
            expire_time = datetime.now() + timedelta(hours=24)

        cookie_data = {
            'cookies': cookie_dict,
            'expire_time': expire_time.isoformat(),
            'base_url': base_url,
            'env_name': env_name,
            'username': username,
            'save_time': datetime.now().isoformat()
        }

        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_data, f, ensure_ascii=False, indent=2)

        return cookie_file

    def load_cookie_data(self, env_name: str, username: str) -> Optional[Dict[str, Any]]:
        """
        加载cookie数据（不进行过期检查）
        :param env_name: 环境名称
        :param username: 用户名
        :return: cookie数据
        """
        cookie_file = self.get_cookie_file_path(env_name, username)

        if not os.path.exists(cookie_file):
            return None

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)

            # 转换时间字符串回datetime对象（如果需要）
            if 'expire_time' in cookie_data:
                cookie_data['expire_time_dt'] = datetime.fromisoformat(cookie_data['expire_time'])
            if 'save_time' in cookie_data:
                cookie_data['save_time_dt'] = datetime.fromisoformat(cookie_data['save_time'])

            return cookie_data

        except (json.JSONDecodeError, ValueError, IOError) as e:
            print(f"加载Cookie数据失败: {e}")
            # 删除损坏的cookie文件
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
            return None

    def load_cookies(self, env_name: str, username: str) -> Optional[requests.cookies.RequestsCookieJar]:
        """
        加载cookies对象（不进行过期检查）
        :param env_name: 环境名称
        :param username: 用户名
        :return: cookies对象
        """
        cookie_data = self.load_cookie_data(env_name, username)
        if not cookie_data or 'cookies' not in cookie_data:
            return None

        # 转换回RequestsCookieJar
        cookies = requests.cookies.RequestsCookieJar()
        for name, value in cookie_data['cookies'].items():
            cookies.set(name, value)

        return cookies

    def is_cookie_expired(self, env_name: str, username: str) -> bool:
        """
        检查cookie是否过期
        :param env_name: 环境名称
        :param username: 用户名
        :return: 是否过期
        """
        cookie_data = self.load_cookie_data(env_name, username)
        if not cookie_data or 'expire_time' not in cookie_data:
            return True

        try:
            expire_time = datetime.fromisoformat(cookie_data['expire_time'])
            return datetime.now() > expire_time
        except (ValueError, TypeError):
            return True

    def get_cookie_info(self, env_name: str, username: str) -> Optional[Dict[str, Any]]:
        """
        获取cookie的详细信息（包含过期状态）
        :param env_name: 环境名称
        :param username: 用户名
        :return: cookie的详细信息字典
        """
        cookie_data = self.load_cookie_data(env_name, username)
        if not cookie_data:
            return None

        # 添加过期状态信息
        cookie_data['is_expired'] = self.is_cookie_expired(env_name, username)
        return cookie_data

    def clear_cookies(self, env_name: str, username: str):
        """
        清除指定环境和用户的cookie文件
        :param env_name: 环境名称
        :param username: 用户名
        :return: None
        """
        cookie_file = self.get_cookie_file_path(env_name, username)
        if os.path.exists(cookie_file):
            os.remove(cookie_file)
            print(f"已清除{env_name}环境{username}用户的Cookie缓存")

    def clear_all_cookies(self):
        """清除所有cookie文件"""
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path) and filename.endswith('.json'):
                os.remove(file_path)
        print(f"已清除{self.cache_dir}目录下的所有Cookie缓存")


if __name__ == '__main__':
    # 使用示例
    manager = CookieManager("my_service")

    # 模拟一些cookies
    test_cookies = requests.cookies.RequestsCookieJar()
    test_cookies.set('session_id', 'abc123')
    test_cookies.set('user_token', 'xyz789')

    # 保存cookies
    file_path = manager.save_cookies(
        env_name="dev",
        username="test_user",
        base_url="https://example.com",
        cookies=test_cookies,
        expire_time=datetime.now() + timedelta(hours=2)
    )
    print(f"Cookie保存到: {file_path}")

    # 加载cookie数据（不检查过期）
    cookie_data = manager.load_cookie_data("dev", "test_user")
    print("Cookie数据:", cookie_data)

    # 检查是否过期
    is_expired = manager.is_cookie_expired("dev", "test_user")
    print(f"Cookie是否过期: {is_expired}")

    # 获取详细信息
    info = manager.get_cookie_info("dev", "test_user")
    print("Cookie详细信息:", info)

    # 加载cookies对象
    cookies = manager.load_cookies("dev", "test_user")
    print("Cookies对象:", dict(cookies))
