# =========================MySQL数据库的配置=======================
import os

DATABASE = {
    'host': '127.0.0.1',
    'port': '3306',
    'user': 'root',
    'database': 'fastapi',
    'password': 'hubangguo199780',
}

# =========================RabbitMQ的配置=======================
MQ_CONFIG = {
    'host': '127.0.0.1',
    'port': 5672,
    'username': 'guest',
    'password': 'guest',
    "heartbeat": 600,
    'blocked_connection_timeout': 300,
}

# ==========================Redis的配置==========================
REDIS_CONFIG = {
    'host': '127.0.0.1',
    'port': 6379,
    'db': 15,
    'password': ''
}

# ==========================APScheduler的配置==========================
APScheduler_CONFIG = {
    'host': '127.0.0.1',
    'port': 6379,
    'db': 7,  # 默认UI任务队列
    'password': '',
    'api_db': 8,  # api测试任务
}

# 项目中所有应用的models
INSTALLED_APPS = [
    'auth.user.models',
    'auth.permission.models',  # 权限控制
    'wealth.device.models',
    'wealth.environment.models',
    'wealth.module.models',
    'wealth.project.models',
    'uiTest.case.models',
    'uiTest.cronjob.models',
    'uiTest.suite.models',
    'uiTest.task.models',
    'uiTest.runner.models',
    'apiTest.apiCase.models',  # api测试用例
    'apiTest.apiSuite.models',  # api测试套件
    'apiTest.task.models',  # api测试任务
    'apiTest.apiCronjob.models',  # api测试任务
    'apiTest.apiRecordExecution.models',  # api测试用例执行记录
    'userDict.models',  # 用户字典
]

# TORTOISE_ORM配置
TORTOISE_ORM = {
    # 数据库配置
    'connections': {
        'default': {
            'engine': 'tortoise.backends.mysql',
            'credentials': DATABASE
        }
    },
    # 启用时区支持
    "timezone": "Asia/Shanghai",
    # 应用配置
    'apps': {
        'models': {
            'models': ['aerich.models', *INSTALLED_APPS],
            'default_connection': 'default'
        },
    }
}

# ==========================token的配置========================
# 64位秘钥
SECRET_KEY = "8beac45e868942b7157e25a0396f36db16ea92dd6713c9ebd116c5259e3fb3d3"
# 加密算法
ALGORITHM = "HS256"
# token过期时间默认1天
TOKEN_TIMEOUT = 60 * 60 * 24 * 1
DEVICE_PORT = 9001  # 设备端口
# 设备心跳检测时间间隔
HEARTBEAT_CHECK_INTERVAL = 60

# ==========================nh-ai的配置========================

NHAI_CONFIG = {
    'default_user': 'jda003',
    'default_password': '',
    'base_url': 'https://api-test.neurohome-ai.com'
}
# ==========================综服的配置========================

SERVICE_PLATFORM_CONFIG = {
    'username': 'dhcpmtest1',  # 综合服务平台用户名
    'password': ''  # 密码
}

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(BASE_DIR)
