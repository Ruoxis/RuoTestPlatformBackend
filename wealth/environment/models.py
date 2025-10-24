from tortoise import fields, models


class Environment(models.Model):
    """环境的模型类"""
    id = fields.IntField(pk=True, description="环境id", max_length=100)
    name = fields.CharField(max_length=255, description="环境名称")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    project = fields.ForeignKeyField("models.Project", related_name="environment", description="所属项目")
    host = fields.CharField(max_length=255, description="环境地址")
    global_vars = fields.JSONField(description="全局变量", default=dict)
    username = fields.CharField(max_length=50, description="创建人")

    def __str__(self):
        return self.name

    class Meta:
        table = "environment"
        table_description = "测试环境"
