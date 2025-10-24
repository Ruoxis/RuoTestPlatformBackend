import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, HTTPException, Depends, status
from .models import ApiCronjob
from .schemas import CronjobForm, CronjobUpdateForm
from wealth.project.models import Project
from wealth.environment.models import Environment
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz
from common import settings
from auth.auth import is_authenticated
from tortoise import transactions
from common.mq_producer import MQProducer
from wealth.device.models import Device

from ..apiCase.models import ApiCase
from ..apiRecordExecution.models import ApiTaskRunRecord, ApiSuiteRunRecord, ApiCaseRunRecord
from ..apiSuite.models import ApiTestSuite
from ..task.models import ApiTask

# 创建路由对象
router = APIRouter(tags=["定时任务"], dependencies=[Depends(is_authenticated)])

# 配置APScheduler存储器
job_stores = {
    'default': RedisJobStore(host=settings.APScheduler_CONFIG['host'], port=settings.APScheduler_CONFIG['port'],
                             db=settings.APScheduler_CONFIG['api_db'], password=settings.APScheduler_CONFIG['password'])
}
# 任务执行器，使用异步调度时不需要配置
# executors = {'default': ThreadPoolExecutor(20)}
# 创建job时的默认参数
job_defaults = {'coalesce': False, 'max_instances': 10}
# 时区
local_timezone = pytz.timezone('Asia/Shanghai')
# 创建调度器
# 使用AsyncIOScheduler来支持异步任务函数
api_scheduler = AsyncIOScheduler(jobstores=job_stores, job_defaults=job_defaults, timezone=local_timezone)


async def run_task_async(task_id, env_id, cronjob_type):
    """
    异步提交任务到rabbitmq中
    :param task_id: 任务id
    :param env_id: 环境id
    :param cronjob_type: 定时任务类型
    :return:
    """
    # 获取测试套件数据
    task = await ApiTask.get_or_none(id=task_id).prefetch_related('suites', 'project')
    if not task:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试计划不存在！")

    # 获取测试环境
    env = await Environment.get_or_none(id=env_id)
    if not env:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试环境不存在！")

    # 获取第一个在线设备
    device = await Device.filter(status="在线").first()
    if not device:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="在线设备不存在！")

    # 获取设备id
    device_id = device.id
    # 组装执行的数据
    env_config = {
        "is_debug": False,
        "host": env.host,
        "global_variable": env.global_vars,
        "timeout": 30,
        "verify_ssl": True,
        "auth_type": "none",
    }

    # 创建一条任务执行的记录
    task_record = await ApiTaskRunRecord.create(task=task, username=task.username, env=env_config, project=task.project)
    task_count = 0
    mq = MQProducer(is_api=True)
    # case_create_user_name = case_.create_user.username if case_ and case_.create_user else "未知用户"
    # 获取测试计划的套件数据
    for suite in await task.suites.all():
        cases = []
        # 获取遍历出来套件中的用例数据
        suite_ = await ApiTestSuite.get_or_none(id=suite.id)
        if not suite_:
            continue

        # 创建套件的运行记录
        suite_record = await ApiSuiteRunRecord.create(suite=suite_, username=task.username, env=env_config,
                                                      task_records=task_record)

        for index, suite_case in enumerate(suite_.cases_order):
            # suite_case_data = json.loads(suite_case)
            case_ = await ApiCase.get_or_none(id=suite_case.get('id'))
            # 创建一条执行记录
            case_record = await ApiCaseRunRecord.create(case=case_, username=task.username,
                                                        suite_records=suite_record,
                                                        env=env_config)
            cases.append({
                "record_id": case_record.id,
                'id': case_.id,
                'name': case_.case_name,
                "skip": suite_case.get('skip', False),
                "steps": index
            })

        task_count += len(cases)
        suite_record.all = len(cases)
        await suite_record.save()

        run_suite = {
            'id': suite_.id,
            'suite_record_id': suite_record.id,
            'task_record_id': task_record.id,
            'name': suite_.suite_name,
            "username": task.username,
            "variables": suite_.variables,  # 公共变量
            "config": suite_.config,  # 公共配置
            "reset_cache": True,  # 是否重置缓存
            # 测试套件的公共前置操作
            'setup_step': suite_.suite_setup_step,
            "cases": cases,
            "cronjob_type": cronjob_type,
        }

        mq.send_api_test_task(env_config=env_config, run_case=run_suite, device_id=device_id)
    # 关闭MQ连接
    mq.close()

    # 修改任务中的用例总数
    task_record.all = task_count
    await task_record.save()

    return {"msg": "API定时任务已经提交到对应的设备，等待执行完毕！", "task_record_id": task_record.id}


# 创建定时任务
@router.post("/cronjob", summary="创建定时任务", status_code=status.HTTP_201_CREATED)
async def create_cronjob(item: CronjobForm):
    if item.cronjob_type != 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="任务类型错误")
    # 获取测试计划
    task = await ApiTask.get_or_none(id=item.task)
    if not task:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="测试计划参数有误，不存在对应的任务")
    # 获取测试环境
    env = await Environment.get_or_none(id=item.env)
    if not env:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="测试环境参数有误，不存在对应的环境")
    # 获取测试项目
    project = await Project.get_or_none(id=item.project)
    if not project:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="测试计划参数有误，不存在对应的项目")
    # 校验任务类型
    if item.run_type not in ["Interval", "date", "crontab"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="任务类型参数不存在")
    # 转换为datatime格式
    date_obj = datetime.datetime.strptime(item.date, "%Y-%m-%d %H:%M:%S")
    # 判断时间是否小于当前时间
    if date_obj < datetime.datetime.now():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="指定的执行时间不能小于当前时间")
    # 获取时间戳，取整作为任务ID
    # cronjob_id = str(int(time.time() * 1000))
    cronjob_id = None
    cronjob = None
    # 创建事务
    async with transactions.in_transaction('default') as cronjob_transaction:
        try:
            # 判断任务类型
            if item.run_type == "date":
                # 创建触发器
                trigger = DateTrigger(run_date=date_obj, timezone=local_timezone)
            elif item.run_type == "crontab":
                trigger = CronTrigger(**item.crontab.model_dump(), timezone=local_timezone)
            elif item.run_type == "Interval":
                trigger = IntervalTrigger(seconds=item.interval, timezone=local_timezone)
            else:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="定时任务类型参数错误")
            # 创建定时任务记录
            cronjob = await ApiCronjob.create(name=item.name, username=item.username,
                                              project_id=item.project, env_id=item.env, task_id=item.task,
                                              run_type=item.run_type, interval=item.interval,
                                              date=date_obj.strftime("%Y-%m-%d %H:%M:%S"),
                                              crontab=item.crontab.model_dump(), state=item.state,
                                              cronjob_type=item.cronjob_type
                                              )
            # 创建定时任务调度器
            cronjob_id = str(cronjob.id)
            # 直接使用run_task_async函数，避免事件循环冲突
            api_scheduler.add_job(func=run_task_async, trigger=trigger, id=cronjob_id, name=item.name,
                                  # 任务id、# 环境id、#
                                  kwargs={'task_id': item.task, 'env_id': item.env, "cronjob_type": item.cronjob_type},
                                  misfire_grace_time=30)
        except Exception as e:
            # 取消定时任务调度器（只有在cronjob_id不为None时才尝试移除）
            if cronjob_id is not None and api_scheduler.get_job(job_id=cronjob_id):
                api_scheduler.remove_job(job_id=cronjob_id)
            # 如果创建定时任务调度器失败，则回滚事务
            await cronjob_transaction.rollback()
            # 记录详细错误信息
            error_detail = f"定时任务创建失败: {str(e)}"
            if hasattr(e, '__cause__') and e.__cause__:
                error_detail += f", 原因: {str(e.__cause__)}"

            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"定时任务调度器创建失败，请检查参数{str(error_detail)}")
        else:
            # 将时间改成utc时间保存
            item.date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            # 定时任务调度器状态判断
            try:
                # 判断任务的状态
                if cronjob.state:
                    api_scheduler.resume_job(job_id=cronjob_id)
                else:
                    api_scheduler.pause_job(job_id=cronjob_id)
                # 保存定时任务调度器
                await cronjob.save()
            except Exception as e:
                if api_scheduler.get_job(job_id=cronjob_id):
                    api_scheduler.remove_job(job_id=cronjob_id)
                await cronjob_transaction.rollback()

                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"修改任务状态失败: {str(e)}")
            # 提交事务
            await cronjob_transaction.commit()
            return cronjob


# 获取定时任务列表
@router.get("/cronjob", summary="定时任务列表", status_code=status.HTTP_200_OK)
async def get_cronjob(page: int = 1, size: int = 10, search=None, cronjob_type: int = 1, project_id: int | None = None):
    """
    获取定时任务列表
    :param page: 页码
    :param size: 每页数量
    :param search: 搜索关键字
    :param cronjob_type: 定时任务类型
    :param project_id: 所属项目id
    :return:
    """
    if cronjob_type != 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="任务类型错误")
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试项目不存在")
    query = ApiCronjob.filter(project_id=project_id).all().order_by("-id")
    if search:
        query = query.filter(name__icontains=search)

    cronjobs = await query.offset((page - 1) * size).limit(size)
    total = await query.count()
    result = []
    for cronjob in cronjobs:
        env = await cronjob.env.all()
        task = await cronjob.task.all()
        result.append({
            "id": cronjob.id,
            "name": cronjob.name,
            "username": cronjob.username,
            "create_time": cronjob.create_time,
            "update_time": cronjob.update_time,
            "run_type": cronjob.run_type,
            "interval": cronjob.interval,
            "date": cronjob.date,
            "crontab": cronjob.crontab,
            "state": cronjob.state,
            "cronjob_type": cronjob.cronjob_type,
            "task": task.id,
            "env": env.id,
            "env_name": env.name,
            "task_name": task.name
        })
    return {
        "data": result,
        "total": total
    }


# 删除定时任务
@router.delete("/cronjob/{cronjob_id}/{cronjob_type}", summary="删除定时任务", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cronjob(cronjob_id: str, cronjob_type: int):
    if cronjob_type != 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="任务类型错误")
    cronjob = await ApiCronjob.get_or_none(id=cronjob_id)
    if not cronjob:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="定时任务不存在")
    else:
        # 删除定时任务调度器
        if api_scheduler.get_job(job_id=cronjob_id):  # 先检查任务是否存在
            api_scheduler.remove_job(job_id=cronjob_id)
        # 删除定时任务记录
        await cronjob.delete()


# 切换定时任务状态
@router.put("/cronjob/switch/{cronjob_id}", summary="修改定时任务状态", status_code=status.HTTP_200_OK)
async def switch_cronjob(cronjob_id: str):
    # 尝试获取定时任务
    cronjob = await ApiCronjob.get_or_none(id=cronjob_id)
    # 判断定时任务是否存在
    if not cronjob:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="定时任务不存在")
    # 创建事务
    async with transactions.in_transaction('default') as cronjob_transaction:
        # 暂停定时任务调度器
        try:
            cronjob.state = not cronjob.state
            # 判断任务的状态
            if api_scheduler.get_job(job_id=cronjob_id):  # 先检查任务在调度器中是否存在
                if cronjob.state:
                    api_scheduler.resume_job(job_id=cronjob_id)
                else:
                    api_scheduler.pause_job(job_id=cronjob_id)
            # 保存定时任务调度器
            await cronjob.save()
        except Exception as e:
            await cronjob_transaction.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"修改任务状态失败: {str(e)}")
        else:
            # 提交事务
            await cronjob_transaction.commit()
        return cronjob


# 修改定时任务的配置
@router.put("/cronjob/{cronjob_id}", summary="修改定时任务配置", status_code=status.HTTP_200_OK)
async def update_cronjob(cronjob_id: int, item: CronjobUpdateForm):
    cronjob = await ApiCronjob.get_or_none(id=cronjob_id)
    # 判断定时任务是否存在
    if not cronjob:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="定时任务不存在")
    # 校验任务类型
    if item.run_type not in ["Interval", "date", "crontab"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="修改的任务类型不存在")
    # 校验时间格式
    date_obj = datetime.datetime.strptime(item.date, "%Y-%m-%d %H:%M:%S")
    if date_obj < datetime.datetime.now():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="修改的时间不能小于当前时间")
    # 创建事务
    async with transactions.in_transaction('default') as cronjob_transaction:
        try:
            if item.run_type == "date":
                trigger = DateTrigger(run_date=date_obj, timezone=local_timezone)
            elif item.run_type == "crontab":
                trigger = CronTrigger(**item.crontab.model_dump(), timezone=local_timezone)
            elif item.run_type == "Interval":
                trigger = IntervalTrigger(seconds=item.interval, timezone=local_timezone)
            else:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="定时任务类型参数错误")

            # 获取任务参数
            task_id = cronjob.task_id
            env_id = cronjob.env_id

            # 更新定时任务调度器
            # 先检查任务是否存在，如果不存在则先创建
            cronjob_id_str = str(cronjob_id)
            if api_scheduler.get_job(job_id=cronjob_id_str):
                api_scheduler.modify_job(job_id=cronjob_id_str, trigger=trigger,
                                         kwargs={'task_id': task_id, 'env_id': env_id,
                                                 "cronjob_type": item.cronjob_type})
            else:
                # 如果调度器中不存在该任务，则添加新任务
                # 直接使用run_task_async函数，避免事件循环冲突
                api_scheduler.add_job(func=run_task_async, trigger=trigger, id=cronjob_id_str, name=cronjob.name,
                                      kwargs={'task_id': task_id, 'env_id': env_id, "cronjob_type": item.cronjob_type})

            # 将时间改成utc时间保存
            item.date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            # 更新定时任务记录
            await cronjob.update_from_dict(item.model_dump(exclude_unset=True)).save()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"修改定时任务失败{str(e)}")
        else:
            # 提交事务
            await cronjob_transaction.commit()
        return cronjob
