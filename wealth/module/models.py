from tortoise import fields, models


class Module(models.Model):
    """项目模块"""
    id = fields.IntField(pk=True, description="模块id", max_length=100, auto_increment=True)
    name = fields.CharField(max_length=255, description="模块名称")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    project = fields.ForeignKeyField("models.Project", related_name="module", description="所属项目")
    username = fields.CharField(max_length=50, description="创建人")

    def __str__(self):
        return self.name

    class Meta:
        table = "module"
        table_description = "项目模块"
