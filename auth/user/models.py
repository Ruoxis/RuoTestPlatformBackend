from tortoise import models, fields


class User(models.Model):
    """用户模型"""
    id = fields.IntField(pk=True, auto_increment=True, description="用户id", max_length=100)
    username = fields.CharField(max_length=50, description="用户名")
    password = fields.CharField(max_length=255, description="密码")
    nickname = fields.CharField(max_length=50, description="用户昵称")
    email = fields.CharField(max_length=50, description="邮箱", default="")
    mobile = fields.CharField(max_length=11, description="手机号", default="")
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_superuser = fields.BooleanField(default=False, description="是否超级管理员")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    def __str__(self):
        return self.nickname

    class Meta:
        table = "user"
        table_description = "用户列表"
