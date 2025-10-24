from tortoise import models, fields


class Device(models.Model):
    """执行设备"""
    id = fields.CharField(description="设备id", max_length=100, pk=True, auto_increment=True)
    ip = fields.CharField(description="设备ip", max_length=50)
    name = fields.CharField(description="设备名称", max_length=50)
    system = fields.CharField(description="操作系统", max_length=50)
    status = fields.CharField(description="设备状态", max_length=50, defualt='在线',
                              choices=["在线", "离线", "忙碌", "故障"])
    username = fields.CharField(description="创建人", max_length=50)
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    update_time = fields.DatetimeField(auto_now=True, description="更新时间")
    version = fields.CharField(description="设备版本", max_length=250)
    hostname = fields.CharField(description="设备主机名", max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        table = "device"
        table_description = "执行设备"
