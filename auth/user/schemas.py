from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List
import re
from auth import auth
from auth.auth import sogal_login
from common.factory_pattern import AsyncValidatedModel
from common.src.unit.method_tools import ValidatedError
from .models import User


class LoginForm(AsyncValidatedModel):
    """登录的表单"""
    username: str = Field(description="用户名", min_length=2, max_length=18)
    password: str = Field(description="密码", min_length=6, max_length=18)

    async def async_validate(self):
        """异步验证唯一性"""
        user_info = await sogal_login(self.username, self.password)
        if user_info.get("state"):
            user = await User.get_or_none(username=self.username)
            if not user:
                register_data = RegisterForm(
                    username=self.username,
                    password=self.password,
                    password_confirm=self.password,
                    nickname=user_info.get("nickname"),
                    email=user_info.get("email"),
                    mobile=user_info.get("mobile")
                )
                user = await register_user(register_data)
                return {"valid": user_info.get("state"),
                        "data": user}
            else:
                return {"valid": user_info.get("state"),
                        "data": user}
        else:  # oa 验证失败
            user = await User.get_or_none(username=self.username)
            if not user:  # 看看是否为本系统自用户
                return {
                    "valid": user_info.get("state"),
                    "message": user_info.get("msg")
                }
            else:  # 本系统用户验证
                if not auth.verify_password(self.password, user.password):
                    return {
                        "valid": user_info.get("state"),
                        "message": "用户名或密码错误，提示：您可使用OA账号密码登录！"
                    }
                else:
                    return {"valid": True,
                            "data": user}


class RegisterForm(AsyncValidatedModel):
    """注册的表单"""
    username: str = Field(description="用户名", min_length=2, max_length=18)
    password: str = Field(description="密码", min_length=6, max_length=18)
    password_confirm: str = Field(description="确认密码", min_length=6, max_length=18)
    email: str = Field(description="邮箱")
    mobile: str = Field(description="手机号", min_length=11, max_length=11)
    nickname: str = Field(description="用户昵称", min_length=2, max_length=18)

    @validator('email')
    def validate_email_format(cls, v):
        """同步验证邮箱格式"""
        if not re.fullmatch(r"^[^@]+@[^@]+\.[^@]+", v):
            raise ValidatedError('邮箱格式不正确')
        return v

    @validator('mobile')
    def validate_mobile_format(cls, v):
        """同步验证手机号格式"""
        if not re.fullmatch(r"^1\d{10}$", v):
            raise ValidatedError('手机号格式不正确')
        return v

    async def async_validate(self):
        """异步验证唯一性"""
        username_exists = await User.get_or_none(username=self.username)
        email_exists = await User.get_or_none(email=self.email)
        mobile_exists = await User.get_or_none(mobile=self.mobile)
        if self.password != self.password_confirm:
            raise ValidatedError(f"两次密码不一致")
        if username_exists:
            raise ValidatedError(f"用户名已存在")
        if email_exists:
            raise ValidatedError(f"邮箱已存在")
        if mobile_exists:
            raise ValidatedError(f"手机号已存在")
        return self


async def register_user(register_data: RegisterForm):
    # 密码加密
    password = auth.get_password_hash(register_data.password)
    user = await User.create(
        username=register_data.username,
        password=password,
        nickname=register_data.nickname,
        email=register_data.email,
        mobile=register_data.mobile
    )

    # 为新用户在所有项目中分配"其他用户"角色
    from auth.permission.models import Role, ProjectRole
    from wealth.project.models import Project
    
    # 获取"其他用户"角色
    other_user_role = await Role.get_or_none(name="其他用户")
    if other_user_role:
        # 获取所有项目
        projects = await Project.all()
        # 为用户在每个项目中分配"其他用户"角色
        for project in projects:
            await ProjectRole.get_or_create(
                user=user,
                project=project,
                defaults={
                    'role': other_user_role,
                    'granted_by': None  # 系统自动分配
                }
            )

    return UserSchemas(**user.__dict__)


class UserSchemas(BaseModel):
    """用户的模型类"""
    id: int = Field(description="用户id")
    username: str = Field(description="用户名")
    nickname: str = Field(description="用户昵称")
    email: str = Field(description="邮箱")
    mobile: str = Field(description="手机号", min_length=11, max_length=11)
    is_active: bool = Field(description="是否激活")
    is_superuser: bool = Field(description="是否超级管理员")
    created_at: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")


class UserListSchemas(BaseModel):
    """用户列表的模型类"""
    total: int = Field(description="总数")
    data: List[UserSchemas] = Field(description="数据")


class LoginSchemas(BaseModel):
    """登录的模型类"""
    token: str = Field(description="访问令牌")
    user: UserSchemas


class RegisterSchemas(BaseModel):
    """注册的模型类"""
    mobile: str = Field(description="手机号")
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱")
    nickname: str = Field(description="用户昵称")


class TokenForm(BaseModel):
    """token的表单"""
    token: str = Field(description="token")


class Token(BaseModel):
    """接口文档的鉴权使用"""
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(description="令牌类型")


if __name__ == '__main__':
    pass
