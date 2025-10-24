from tortoise import models, fields


class Role(models.Model):
    """角色表"""
    id = fields.IntField(pk=True, auto_increment=True, description="角色id")
    name = fields.CharField(max_length=50, description="角色名称", unique=True)
    description = fields.CharField(max_length=255, description="角色描述", default="")
    level = fields.IntField(description="角色等级 1:系统管理员 2:项目管理员 3:项目成员 4:其他用户 5:自定义角色")
    is_system = fields.BooleanField(default=False, description="是否为系统内置角色")
    is_active = fields.BooleanField(default=True, description="是否启用")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    def __str__(self):
        return self.name

    class Meta:
        table = "role"
        table_description = "角色表"


class Permission(models.Model):
    """权限表"""
    id = fields.IntField(pk=True, auto_increment=True, description="权限id")
    name = fields.CharField(max_length=50, description="权限名称", unique=True)
    code = fields.CharField(max_length=100, description="权限代码", unique=True)
    description = fields.CharField(max_length=255, description="权限描述", default="")
    category = fields.CharField(max_length=50, description="权限分类", default="")
    is_active = fields.BooleanField(default=True, description="是否启用")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    def __str__(self):
        return self.name

    class Meta:
        table = "permission"
        table_description = "权限表"


class ProjectRole(models.Model):
    """项目角色关联表 - 用户在某个项目下的角色"""
    id = fields.IntField(pk=True, auto_increment=True, description="id")
    user = fields.ForeignKeyField(
        model_name="models.User",
        related_name="project_roles",
        description="用户",
        on_delete=fields.CASCADE
    )
    project = fields.ForeignKeyField(
        model_name="models.Project",
        related_name="user_roles",
        description="项目",
        on_delete=fields.CASCADE
    )
    role = fields.ForeignKeyField(
        model_name="models.Role",
        related_name="project_users",
        description="角色",
        on_delete=fields.CASCADE
    )
    granted_by = fields.ForeignKeyField(
        model_name="models.User",
        related_name="granted_roles",
        description="授权人",
        on_delete=fields.CASCADE,
        null=True
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")

    def __str__(self):
        return f"{self.user.username} - {self.project.name} - {self.role.name}"

    class Meta:
        table = "project_role"
        table_description = "项目角色关联表"
        unique_together = ("user", "project")


class RolePermission(models.Model):
    """角色权限关联表"""
    id = fields.IntField(pk=True, auto_increment=True, description="id")
    role = fields.ForeignKeyField(
        model_name="models.Role",
        related_name="permissions",
        description="角色",
        on_delete=fields.CASCADE
    )
    permission = fields.ForeignKeyField(
        model_name="models.Permission",
        related_name="roles",
        description="权限",
        on_delete=fields.CASCADE
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"

    class Meta:
        table = "role_permission"
        table_description = "角色权限关联表"
        unique_together = ("role", "permission")