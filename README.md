## 部署

### 安装依赖包

    安装 RabbitMQ
    安装 redis
    安装 python3.11 main.py
    pip install -r requirements.txt

### 修改 common.settings.py 的中的配置

```python
# =========================数据库的配置信息=======================
DATABASE = {
    'host': 'localhost',
    'port': '3306',
    'user': 'root',
    'password': 'mysql',
    'database': 'webtest001',
}
# =========================RabbitMQ的配置=====================================

MQ_CONFIG = {
    'host': '127.0.0.1',
    'port': 5672,
    'queue': 'web_test_queue',  # 任务队列名称，需要和分布式节点一致
}

# ==========================redis的配置=====================================
# redis配置
REDIS_CONFIG = {
    'host': '127.0.0.1',
    'port': 6379,
    'db': 5,
}

```

### 数据库配置

    在数据库中创建database指定的库，上面的数据库为 webtest001
    生成迁移文件：aerich init -t common.settings.TORTOISE_ORM
    执行迁移，生成数据库表：aerich init-db

    # 模型发生修改后
    aerich migrate 生成新的迁移
    aerich upgrade 执行迁移

### 运行main.py启动项目

    上面的环境安装好之后，运行main.py 即可启动项目。
    项目运行之后即可访问在线 openAPI 接口文档地址：
    接口文档地址：http://127.0.0.1:8000/dosc。
    可以通过openAPI接口文档里面注册接口注册一个账号

## 提交规范

    ✨ feat：新功能
    🐛 fix：问题修复
    📚 docs：文档更新
    🎨 style：代码样式调整
    🔧 refactor：重构（不改变功能）
    🚀 perf：性能优化
    ✅ test：测试相关
    🛠️ chore：构建/工具变更