from passlib.context import CryptContext
from fastapi import HTTPException, Depends
import time
import jwt
from common import settings
from fastapi.security import OAuth2PasswordBearer
from common.src.unit.method_tools import MethodTools
from common.src.unit.sogal_login import UmasProperties, LdapUtils

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


async def is_authenticated(token: str = Depends(oauth2_scheme)) -> dict:
    """校验token中的用户信息"""
    return verify_token(token)


def create_token(userinfo: dict):
    # 过期时间
    expire = int(time.time()) + settings.TOKEN_TIMEOUT
    userinfo['exp'] = expire
    # 使用pyjwt生成token
    return jwt.encode(userinfo, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token):
    """校验token"""
    if not token or token.count('.') != 2:
        raise HTTPException(status_code=401, detail="token校验失败或者无效token")
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
        return data
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token校验失败或者无效token！")


def verify_password(plain_password, hashed_password):
    """
    校验密码
    :param plain_password: 明文密码
    :param hashed_password: 密文密码
    :return:
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    哈希密码
    :param password: 明文密码
    :return:
    """
    return pwd_context.hash(password)


async def sogal_login(username, password):
    try:
        if not username.isdigit():
            return {
                "state": False,
                "msg": "用户名格式错误，请输入数字形式的OA账号"
            }
        # 创建配置对象
        user_props = UmasProperties()
        # 获取用户信息
        user_info = await LdapUtils.get_user(user_props, username, password)
        return {
            "state": True,
            "msg": "登录成功",
            "email": user_info.get('mail', ''),
            "nickname": user_info.get('displayName', ''),
            "username": username,
            "password": password,
            "mobile": MethodTools.format_phone_smart(username)
        }
    except Exception as e:
        return {
            "state": False,
            "msg": f"登录失败: {e}"
        }
