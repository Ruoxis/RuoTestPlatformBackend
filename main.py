import os
import click
import json
import asyncio
import logging
import uvicorn
import logging.handlers
from common import settings
from uvicorn.config import LOGGING_CONFIG
from contextlib import asynccontextmanager
from starlette.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise
from common.src.unit.method_tools import ValidatedError
from starlette.exceptions import HTTPException as StarletteHTTPException

from auth.user.api import router as user_router
from auth.permission.api import router as permission_router

from wealth.module.api import router as module_router
from wealth.device.api import router as device_router
from wealth.project.api import router as project_router
from wealth.device.heartbeat import check_devices_heartbeat
from wealth.environment.api import router as environment_router

from uiTest.cronjob.api import scheduler
from uiTest.task.api import router as task_router
from uiTest.case.api import router as case_router
from uiTest.suite.api import router as suite_router
from uiTest.runner.api import router as runner_router
from uiTest.cronjob.api import router as cronjob_router

from apiTest.apiCronjob.api import api_scheduler
from apiTest.apiCase.url import router as api_test_router
from apiTest.apiSuite.url import router as api_suite_router
from apiTest.task.url import router as api_test_task_router
from apiTest.apiCronjob.api import router as api_cronjob_router
from apiTest.apiRecordExecution.url import router as api_runner_router

from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html

from tools.api import router as tools_router
from userDict.url import router as user_dict_router

# 修改默认日志格式
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"

# 定义允许的来源列表，本地：http://localhost:8080，线上：https://example.com
ALLOWED_ORIGINS = [
    "http://0.0.0.0:8080",
    "http://localhost:8080"
]
banner = """
 █████╗ ██╗   ██╗████████╗ ██████╗ ███╗   ███╗ █████╗ ████████╗██╗ ██████╗ ███╗   ██╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗████╗ ████║██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
███████║██║   ██║   ██║   ██║   ██║██╔████╔██║███████║   ██║   ██║██║   ██║██╔██╗ ██║
██╔══██║██║   ██║   ██║   ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██║██║   ██║██║╚██╗██║
██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║ ╚═╝ ██║██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
"""
# 检查"logs/py.log"文件夹路径
if not os.path.exists("logs"):
    os.makedirs("logs")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """fastapi项目日志"""
    # 项目启动时执行
    click.echo(banner)
    # 启动调度器
    scheduler.start()
    api_scheduler.start()
    # 获取日志记录器
    logger = logging.getLogger("uvicorn.access")
    logging.getLogger('suds').setLevel(logging.INFO)  # 屏蔽suds日志（计料系统数据获取的垃圾日志）
    logging.getLogger('urllib3').setLevel(logging.INFO)  # 屏蔽suds日志（计料系统数据获取的垃圾日志）
    logging.getLogger('python_multipart').setLevel(logging.INFO)  # 屏蔽apscheduler日志（定时任务日志）
    # 创建滚动文件处理器，最大文件大小为10MB
    handler = logging.handlers.RotatingFileHandler("logs/py.log", mode="a", maxBytes=100 * 1024)
    # 设置日志格式
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    # 添加处理器到记录器
    logger.addHandler(handler)
    # 启动心跳检测任务
    heartbeat_task = asyncio.create_task(check_devices_heartbeat())
    yield
    # 项目结束时执行
    # 停止调度器
    scheduler.shutdown()
    api_scheduler.shutdown()
    for handler in logger.handlers:
        logger.removeHandler(handler)
        handler.close()
    # 关闭时清理
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass


# 线上部署屏蔽接口文档，可以增加参数openapi_url=None
app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, title="WEB测试平台接口文档",
              description="v1.0版接口文档", version="1.0", summary="这个是由fastapi生成的WEB测试平台接口文档")


# 接口文档
@app.get("/swagger", include_in_schema=False)
async def custom_swagger_ui_html():
    """swagger接口文档静态文件"""
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=app.title + " - Swagger UI",
                               oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
                               swagger_js_url="/static/swagger-ui-bundle.js",
                               swagger_css_url="/static/swagger-ui.css")


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    """swagger接口文档"""
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """redoc接口文档"""
    return get_redoc_html(openapi_url=app.openapi_url, title=app.title + " - ReDoc",
                          redoc_js_url="/static/redoc.standalone.js")


# 接口文档的静态文件路径
app.mount("/static", StaticFiles(directory="static"), name="static")


# 注册全局异常处理器
@app.exception_handler(ValidatedError)
async def global_validated_error_handler(request: Request, exc: ValidatedError):
    print('global_validated_error_handler')
    """全局捕获 ValidatedError"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "detail": exc.detail,
            "data": None
        }
    )


@app.exception_handler(StarletteHTTPException)
async def global_exception_handler(request: Request, exc: StarletteHTTPException):
    """全局http响应异常处理"""
    print('global_exception_handler')
    print(
        type(exc)
    )
    if isinstance(exc, ValidatedError):
        print('global_exception_handler__')
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "detail": exc.detail,
                "data": None
            }
        )

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def global_validation_handler(request: Request, exc: RequestValidationError):
    """专门处理请求参数验证错误"""
    print('global_validation_handler')
    errors = [str(item.get('ctx').get('error')) for item in exc.errors() if isinstance(item, dict) and item.get('ctx')]
    if len(errors) == 0:
        errors = [str(exc.errors())]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=json.dumps({
            "code": 422,
            "detail": "参数验证失败",
            "errors": errors
        }, ensure_ascii=False, indent=4)
    )


# CORS跨域问题
app.add_middleware(CORSMiddleware,
                   allow_origins=ALLOWED_ORIGINS,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])

# 注册ORM模型
register_tortoise(app, config=settings.TORTOISE_ORM, modules={"models": ["models"]}, add_exception_handlers=True,
                  generate_schemas=True)

# 注册路由
app.include_router(user_router)
app.include_router(project_router)
app.include_router(environment_router)
app.include_router(module_router)
app.include_router(case_router)
app.include_router(suite_router)
app.include_router(task_router)
app.include_router(runner_router, prefix="/run")
app.include_router(device_router)
app.include_router(cronjob_router)
app.include_router(permission_router)
app.include_router(api_test_router, prefix="/api", tags=["接口用例中心"])
app.include_router(api_suite_router, prefix="/api", tags=["接口套件中心"])
app.include_router(api_test_task_router, prefix="/api", tags=["接口计划中心"])
app.include_router(api_cronjob_router, prefix="/api", tags=["接口任务中心"])
app.include_router(api_runner_router, prefix="/runApi", tags=["接口执行中心"])
app.include_router(user_dict_router, prefix="/userdict", tags=["用户字典中心"])
app.include_router(tools_router, prefix="/tools", tags=["辅助工具"])

if __name__ == '__main__':
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=False)
