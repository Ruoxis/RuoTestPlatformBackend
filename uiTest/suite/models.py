from tortoise import fields, models


class Suite(models.Model):
    """测试套件的模型定义"""
    id = fields.IntField(pk=True, description="套件id", max_length=100)
    name = fields.CharField(max_length=50, description="套件名称")
    project = fields.ForeignKeyField("models.Project", related_name="suites", description="所属项目")
    modules = fields.ForeignKeyField("models.Module", related_name="suites", description="所属模块", null=True,
                                     Blank=True)
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    suite_setup_step = fields.JSONField(description="前置执行步骤", default=list)
    suite_type = fields.CharField(max_length=50, description="套件类型", choices=[("1", "功能"), ("2", "场景")],
                                  default="1")
    username = fields.CharField(max_length=50, description="创建人")

    class Meta:
        table = "suite"
        table_description = "测试套件"


class Step(models.Model):
    """套件中的用例模型定义"""
    id = fields.IntField(pk=True, description="用例id", max_length=100)
    suite = fields.ForeignKeyField("models.Suite", related_name="cases", description="所属套件")
    cases = fields.ForeignKeyField("models.Case", related_name="suites", description="所属用例")
    sort = fields.IntField(description="用例执行顺序", default=0)
    skip = fields.BooleanField(description="是否跳过", default=False)

    class Meta:
        table = "step"
        table_description = "套件中的用例"
