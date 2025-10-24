import multiprocessing

# 工作进程
workers = multiprocessing.cpu_count() * 2 + 1
# 设置守护进程
daemon = True
# 监听内网端口8000
bind = '0.0.0.0:8000'
# 设置为True，开发时用，代码修改会自动重启
reload = False
# gunicorn进程文件名。不能放在容器里面，防止文件存在
pidfile = '/tmp/gunicorn.pid'
# gunicorn日志文件
accesslog = '/app/logs/gunicorn_access.log'
errorlog = '/app/logs/gunicorn_error.log'
# 工作模式
worker_class = 'uvicorn.workers.UvicornWorker'
# 指定每个工作者的线程数
threads = 2
# 设置最大并发量
worker_connections = 2000
# 错误日志的日志级别
loglevel = 'info'
