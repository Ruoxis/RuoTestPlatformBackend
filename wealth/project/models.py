from tortoise import fields, models


class Project(models.Model):
    """项目表模型"""
    id = fields.IntField(pk=True, description="项目id",  max_length=100, auto_increment=True)
    name = fields.CharField(max_length=255, description="项目名称")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    user = fields.ForeignKeyField("models.User", related_name="project", description="项目创建人id")
    username = fields.CharField(max_length=50, description="创建人")

    def __str__(self):
        return self.name

    class Meta:
        # 数据库表名
        table = "project"
        # 数据库表描述
        table_description = "测试项目"
