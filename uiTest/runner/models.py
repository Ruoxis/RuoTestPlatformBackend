from tortoise import fields, models


class TaskRunRecord(models.Model):
    """测试计划运行记录表"""
    id = fields.IntField(pk=True, description="套件记录id", max_length=1000)
    project = fields.ForeignKeyField("models.Project", related_name="task_records", description="所属项目")
    task = fields.ForeignKeyField("models.Task", related_name="task_records", description="执行的任务")
    env = fields.JSONField(description="执行环境", default=dict)
    start_time = fields.DatetimeField(auto_now_add=True, description="开始执行时间")
    duration = fields.FloatField(description="执行时间", default=0)
    status = fields.CharField(max_length=255, description="运行状态",
                              choices=[("等待执行", "等待执行"), ("执行完成", "执行完成"), ("执行中", "执行中")],
                              default="执行中")
    all = fields.IntField(description="总用例数", default=0)
    run_all = fields.IntField(description="执行用例数", default=0)
    no_run = fields.IntField(description="未执行用例数", default=0)
    success = fields.IntField(description="成功用例数", default=0)
    pass_rate = fields.FloatField(description="通过率", default=0)
    task_log = fields.JSONField(description="任务执行日志", default=list)
    fail = fields.IntField(description="失败用例数", default=0)
    error = fields.IntField(description="错误用例数", default=0)
    skip = fields.IntField(description="跳过用例数", default=0)
    username = fields.CharField(max_length=50, description="创建人")

    class Meta:
        table = "task_record"
        table_description = "测试计划运行记录"


class SuiteRunRecord(models.Model):
    """测试套件运行记录表"""
    id = fields.IntField(pk=True, description="记录id", max_length=1000)
    suite = fields.ForeignKeyField("models.Suite", related_name="suite_records", description="执行的套件")
    task_records = fields.ForeignKeyField("models.TaskRunRecord", related_name="suite_records",
                                          description="关联的运行任务记录", null=True, blank=True)
    status = fields.CharField(max_length=255, description="运行状态",
                              choices=[("等待执行", "等待执行"), ("执行中", "执行中"), ("执行完成", "执行完成")],
                              default="执行中")
    all = fields.IntField(description="总用例数", default=0)
    run_all = fields.IntField(description="执行用例数", default=0)
    no_run = fields.IntField(description="未执行用例数", default=0)
    success = fields.IntField(description="成功用例数", default=0)
    fail = fields.IntField(description="失败用例数", default=0)
    error = fields.IntField(description="错误用例数", default=0)
    skip = fields.IntField(description="跳过用例数", default=0)
    start_time = fields.DatetimeField(auto_now_add=True, description="开始执行时间")
    duration = fields.FloatField(description="执行时间", default=0)
    suite_log = fields.JSONField(description="套件执行日志", default=list)
    pass_rate = fields.FloatField(description="通过率", default=0)
    env = fields.JSONField(description="执行环境", default=dict, null=True, blank=True)
    username = fields.CharField(max_length=50, description="创建人")

    class Meta:
        table = "suite_record"
        table_description = "测试套件运行记录"


class CaseRunRecord(models.Model):
    """测试用例运行记录表"""
    id = fields.IntField(pk=True, description="用例记录id", max_length=1000)
    case = fields.ForeignKeyField("models.Case", related_name="case_records", description="执行的用例")
    suite_records = fields.ForeignKeyField("models.SuiteRunRecord", related_name="case_records",
                                           description="关联的运行套件记录", null=True, blank=True, default=None)
    status = fields.CharField(max_length=255, description="运行状态",
                              choices=[("success", "执行成功"), ("fail", "执行失败"),
                                       ("error", "执行错误"), ("skip", "跳过执行"), ("no_run", "未执行"),
                                       ("running", "执行中")], default="running")
    run_info = fields.JSONField(description="用例执行详情", default=dict)
    start_time = fields.DatetimeField(auto_now_add=True, description="开始执行时间")
    env = fields.JSONField(description="执行环境", default=dict)
    username = fields.CharField(max_length=50, description="创建人")

    class Meta:
        table = "case_record"
        table_description = "测试用例运行记录"
