# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：factory_pattern.py
@Time ：2025/7/8 17:59
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from typing import Dict, Any, Union, TypeVar
from pydantic import BaseModel
from fastapi import HTTPException, Depends, status

T = TypeVar('T', bound='AsyncValidatedModel')


class AsyncValidatedModel(BaseModel):
    """所有需要异步验证的模型基类"""

    class AsyncValidatedModel(BaseModel):
        """
        支持三种返回格式的异步验证基类：
        1. 返回模型对象自身
        2. 返回错误字典 {"valid": False, "message": "..."}
        3. 返回成功字典 {"valid": True, "data": ..., "message": "..."}
        """

        async def async_validate(self: T) -> Union[T, Dict[str, Any]]:
            """
            异步验证方法，子类应覆盖此方法
            返回选择：
            - 返回 self (模型对象自身)
            - 返回 {"valid": False, "message": "..."} (验证失败)
            - 返回 {"valid": True, "data": ..., "message": "..."} (验证成功带数据)
            """
            return self  # 默认返回模型自身

    @classmethod
    def depends(cls):
        async def validator(model: cls):
            # 先执行Pydantic同步验证
            try:
                validated = model.model_validate(model.dict())  # @validator装饰的自身的同步校验
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
            # @async_validate装饰的异步校验
            try:
                validation_result = await validated.async_validate()
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
            if isinstance(validation_result, dict):
                if not validation_result.get("valid", True):  # 如果验证失败直接范围字典错误信息
                    return validation_result
                if validation_result.get("data"):  # 如果有数据字段则返回数据
                    return validation_result.get("data")

            return validated

        return Depends(validator)


if __name__ == '__main__':
    pass

    """
    # 验证使用示例
    class LoginModel(AsyncValidatedModel):
        username: str
        password: str

        async def async_validate(self):
            user = await authenticate(self.username, self.password)
            if not user:
                return {
                    "valid": False,
                    "message": "用户名或密码错误"
                }
            if user.power == 1:
                # 返回源数据
                return self
            else:
                # 返回自定义数据
                return {
                    "valid": True,
                    "data": {
                        'mode': self,
                        "user": user,
                        "token": create_token(user)
                    },
                    "message": "登录成功"
                }
    # 不需要单独验证处理数据的可以直接使用BaseModel模型
    class LoginModel(BaseModel):
        username: str
        password: str
    """
