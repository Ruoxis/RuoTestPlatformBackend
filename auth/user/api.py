from .. import auth
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from auth.auth import is_authenticated
from .models import User
from .schemas import RegisterForm, UserSchemas, LoginForm, LoginSchemas, TokenForm, Token, RegisterSchemas, \
    UserListSchemas, register_user

# 创建一个路由对象
router = APIRouter(tags=["用户管理"])


@router.post("/register", summary="用户注册", response_model=UserSchemas, status_code=status.HTTP_201_CREATED)
async def register(item: RegisterForm = RegisterForm.depends()):
    if isinstance(item, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))
    else:
        return await register_user(item)


@router.post("/login", summary="用户登录", response_model=LoginSchemas, status_code=status.HTTP_200_OK)
async def login(item: LoginForm = LoginForm.depends()):
    """用户账号登录"""
    if isinstance(item, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=item.get("message"))
    uinfo = UserSchemas(**item.__dict__)
    # 排除datetime字段
    token_payload = uinfo.model_dump(exclude={"created_at", "update_time"})

    # 账户名密码正确，生成token
    token = auth.create_token(token_payload)
    # 返回token 和用户信息
    return LoginSchemas(token=token, user=uinfo)


# 校验token
@router.post("/verify", summary="校验token", response_model=UserSchemas, status_code=status.HTTP_200_OK)
async def verify_token(item: TokenForm):
    """校验token"""
    userinfo = auth.verify_token(item.token)
    # 从数据库获取完整用户信息
    user = await User.get(id=userinfo.get("id"))
    return UserSchemas(**user.__dict__)


# 刷新token
@router.post("/refresh", summary="刷新token", response_model=TokenForm, status_code=status.HTTP_200_OK)
async def refresh_token(item: TokenForm):
    # 刷新token，获取token中的用户信息
    userinfo = auth.verify_token(item.token)
    # 生成新的token
    return {"token": auth.create_token(userinfo)}


@router.post("/token", summary="模拟登录", response_model=Token, status_code=status.HTTP_200_OK)
async def access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """给接口文档登录生成token"""
    user = await User.get_or_none(username=form_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用户名或密码错误")
    if not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用户名或密码错误")
    uinfo = UserSchemas(**user.__dict__)
    # 排除datetime字段
    token_payload = uinfo.model_dump(exclude={"created_at", "update_time"})
    token = auth.create_token(token_payload)
    return Token(access_token=token, token_type="bearer")


@router.put("/update/{user_id}", summary='更新用户', status_code=status.HTTP_200_OK)
async def update_user(user_id, user: RegisterSchemas, user_info: dict = Depends(is_authenticated)):
    """更新用户信息"""
    # 先检查用户是否存在
    existing_user = await User.get_or_none(id=user_id)
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    
    data = await User.filter(id=user_id).update(username=user.username, email=user.email, nickname=user.nickname,
                                                mobile=user.mobile)
    return data


@router.get("/user", summary='查询用户', response_model=UserListSchemas, status_code=status.HTTP_200_OK)
async def get_user(page: int = 1, size: int = 10, user_info: dict = Depends(is_authenticated)):
    """查询用户"""
    query = User.all().order_by("-id")
    total = await query.count()
    user = await query.offset((page - 1) * size).limit(size)
    result = []
    for i in user:
        result.append(UserSchemas(**i.__dict__))
    return {"total": total, "data": result}


@router.delete("/delete/{user_id}", summary='删除用户', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, user_info: dict = Depends(is_authenticated)):
    """删除用户"""
    data = await User.get_or_none(id=user_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="传入的用户ID不存在")
    await data.delete()
