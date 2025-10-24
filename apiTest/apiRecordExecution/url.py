from fastapi import APIRouter, HTTPException, Depends, status
from wealth.device.models import Device
from wealth.environment.models import Environment
from .schemas import RunForm, SuiteResultSchemas, TaskResultSchemas
from ..apiSuite.models import ApiTestSuite
from ..apiCase.models import ApiCase
from ..task.models import ApiTask
from .models import ApiTaskRunRecord, ApiSuiteRunRecord, ApiCaseRunRecord
from common.mq_producer import MQProducer
from tortoise import transactions
from auth.auth import is_authenticated

# 创建路由对象
router = APIRouter(dependencies=[Depends(is_authenticated)])


# 执行单条用例
@router.post("/case/{case_id}", tags=["测试运行"], summary="执行用例", status_code=status.HTTP_201_CREATED)
async def run_case(case_id: int, item: RunForm):
    async with transactions.in_transaction():
        # 获取用例数据
        case_ = await ApiCase.get_or_none(id=case_id)
        if not case_:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例不存在！")
        # 获取测试环境
        env = await Environment.get_or_none(id=item.env_id)
        if not env:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试环境不存在！")

        # 组装执行的数据
        env_config = {
            "is_debug": False,
            "host": env.host,
            "global_variable": env.global_vars,
            "timeout": 30,
            "verify_ssl": True,
            "auth_type": "none",
        }
        # 创建一条执行记录
        case_record = await ApiCaseRunRecord.create(case=case_, username=item.username, env=env_config)
        run_case = {
            'id': case_.id,
            'name': case_.case_name,
            # 测试套件的公共前置操作
            'setup_step': [],
            "username": item.username,
            "reset_cache": item.reset_cache,  # 是否重置缓存
            "cases": [
                {
                    "record_id": case_record.id,
                    'id': case_.id,
                    'name': case_.case_name,
                    "skip": False,
                    "steps": 0
                }
            ]
        }
        # 获取执行的设备ID
        device_id = item.device_id
        # 判断设备的状态
        device = await Device.get_or_none(id=device_id)
        mq = MQProducer(is_api=True)
        if device and device.status == "在线":
            mq.send_api_test_task(env_config=env_config, run_case=run_case, device_id=device_id)
            mq.close()
        return {"msg": "API用例执行任务已经提交到对应的设备，等待执行完毕！", "record_id": case_record.id}


# 运行测试套件
@router.post("/suite/{suite_id}", tags=["测试运行"], summary="执行套件", status_code=status.HTTP_201_CREATED)
async def run_suite(suite_id: int, item: RunForm):
    async with transactions.in_transaction():
        # 获取测试套件数据
        suite_ = await ApiTestSuite.get_or_none(id=suite_id)
        if not suite_:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试套件不存在！")
        # 获取测试环境
        env = await Environment.get_or_none(id=item.env_id)
        if not env:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试环境不存在！")
        # 获取执行使用的浏览器

        # 组装执行的数据
        env_config = {
            "is_debug": False,
            "host": env.host,
            "global_variable": env.global_vars,
            "timeout": 30,
            "verify_ssl": True,
            "auth_type": "none",
        }
        # 创建套件的运行记录
        suite_record = await ApiSuiteRunRecord.create(suite=suite_, username=item.username, env=env_config)
        # 获取测试套件的用例数据
        cases = []
        for index, suite_case in enumerate(suite_.cases_order):
            case_ = await ApiCase.get_or_none(id=suite_case.get('id'))
            # 创建一条执行记录
            case_record = await ApiCaseRunRecord.create(case=case_, username=item.username, suite_records=suite_record,
                                                        env=env_config)
            cases.append({
                "record_id": case_record.id,
                'id': case_.id,
                'name': case_.case_name,
                "skip": suite_case.get('skip', False),
                "steps": index
            })
        suite_record.all = len(cases)
        await suite_record.save()
        run_suite = {
            'id': suite_.id,
            'suite_record_id': suite_record.id,
            'name': suite_.suite_name,
            'username': item.username,
            "variables": suite_.variables,  # 公共变量
            "config": suite_.config,  # 公共配置
            "reset_cache": item.reset_cache,  # 是否重置缓存
            # 测试套件的公共前置操作
            'setup_step': suite_.suite_setup_step,
            "cases": cases,
            "cronjob_type": 1,
        }
        # 获取执行的设备ID
        device_id = item.device_id
        # 判断设备的状态
        device = await Device.get_or_none(id=device_id)
        mq = MQProducer(is_api=True)
        if device and device.status == "在线":
            mq.send_api_test_task(env_config=env_config, run_case=run_suite, device_id=device_id)
            mq.close()
        return {"msg": "API套件执行任务已经提交到对应的设备，等待执行完毕！", "suite_record_id": suite_record.id}


# 运行测试计划
@router.post("/task/{task_id}", tags=["测试运行"], summary="执行任务", status_code=status.HTTP_201_CREATED)
async def run_task(task_id: int, item: RunForm):
    async with transactions.in_transaction():
        # 获取测试套件数据
        task_ = await ApiTask.get_or_none(id=task_id).prefetch_related('suites', 'project')
        if not task_:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试计划不存在！")
        # 检查测试计划中是否有套件
        suite_count = await task_.suites.all().count()
        if suite_count == 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="测试计划中没有套件，请先在测试计划中添加套件！")
        # 获取测试环境
        env = await Environment.get_or_none(id=item.env_id)
        if not env:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试环境不存在！")

        # 组装执行的数据
        env_config = {
            "is_debug": False,
            "host": env.host,
            "global_variable": env.global_vars,
            "timeout": 30,
            "verify_ssl": True,
            "auth_type": "none",
        }
        # 获取设备列表
        device_ids = []
        if item.device_ids:
            device_ids = item.device_ids
        elif item.device_id:
            device_ids = [item.device_id]
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请提供设备ID或设备ID列表！")

        # 获取在线设备列表
        devices = await Device.filter(id__in=device_ids, status="在线")
        online_device_ids = [device.id for device in devices]

        # 检查是否有在线设备
        if not online_device_ids:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="没有在线的设备可供执行任务！")

        # 创建一条任务执行的记录
        task_record = await ApiTaskRunRecord.create(task=task_, username=item.username, env=env_config,
                                                    project=task_.project)
        task_count = 0
        mq = MQProducer(is_api=True)
        # 获取测试计划的套件数据
        for suite in await task_.suites.all():
            cases = []

            # 获取遍历出来套件中的用例数据
            suite_ = await ApiTestSuite.get_or_none(id=suite.id)
            if not suite_:
                continue
            # 创建套件的运行记录
            suite_record = await ApiSuiteRunRecord.create(suite=suite_, username=item.username,
                                                          env=env_config,
                                                          task_records=task_record)

            for index, suite_case in enumerate(suite_.cases_order):
                print(suite_case)
                print(type(suite_case))
                case_ = await ApiCase.get_or_none(id=suite_case.get('id'))
                # 创建一条执行记录
                case_record = await ApiCaseRunRecord.create(case=case_, username=item.username,
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

            run_suite_ = {
                'id': suite_.id,
                'suite_record_id': suite_record.id,
                'task_record_id': task_record.id,
                'name': suite_.suite_name,
                "username": item.username,
                "variables": suite_.variables,  # 公共变量
                "config": suite_.config,  # 公共配置
                "reset_cache": item.reset_cache,  # 是否重置缓存
                # 测试套件的公共前置操作
                'setup_step': suite_.suite_setup_step,
                "cases": cases,
                "cronjob_type": 1,
            }

            mq.send_api_test_task(env_config=env_config, run_case=run_suite_, device_id=online_device_ids[0])
        # 关闭MQ连接
        mq.close()

        # 修改任务中的用例总数
        task_record.all = task_count
        await task_record.save()
    return {"msg": f"API计划执行任务已经提交到{len(online_device_ids)}个在线设备执行，等待执行完毕！",
            "task_record_id": task_record.id}


# 获取测试计划的运行记录
@router.get("/task/record", tags=["测试运行"], summary="任务运行记录", status_code=status.HTTP_200_OK)
async def get_task_record(project_id: int, task_id: int = None, page: int = 1, size: int = 10):
    # 获取测试计划的运行记录
    query = ApiTaskRunRecord.filter(project=project_id)
    # 判断是否传了任务id
    if task_id:
        query = query.filter(task=task_id)
    # 根据id降序排序
    query = query.order_by("-id")
    # 获取任务执行的记录总数
    total = await query.count()
    # 分页获取数据
    data = await query.offset((page - 1) * size).limit(size).prefetch_related('task')
    result = []
    for i in data:
        result.append({
            "id": i.id,
            "task_id": i.task.id,
            "task_name": i.task.name,
            "username": i.username,
            "start_time": i.start_time,
            "duration": i.duration,
            "status": i.status,
            "run_all": i.run_all,
            "success": i.success,
            "fail": i.fail,
            "error": i.error,
            "skip": i.skip,
            "all": i.all,
            "no_run": i.no_run,
            "env": i.env,
            "pass_rate": i.pass_rate,
            "task_log": i.task_log
        })
    return {"total": total, "data": result}


# 删除测试计划的运行记录
@router.delete('/task/record/{record_id}', tags=['测试运行'], summary='删除任务运行记录',
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_record(record_id: int):
    record = await ApiTaskRunRecord.get_or_none(id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="任务运行记录不存在")
    await record.delete()


# 获取测试套件的运行记录
@router.get("/suite/record", tags=["测试运行"], summary="套件运行记录", status_code=status.HTTP_200_OK)
async def get_suite_record(suite_id: int = None, task_records_id: int = None, page: int = 1, size: int = 10):
    # 获取测试套件的运行记录
    query = ApiSuiteRunRecord.all()
    # 判断是否传了套件id
    if suite_id:
        query = query.filter(suite=suite_id)
    elif task_records_id:
        query = query.filter(task_records=task_records_id)
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="suite_id和task_records_id至少传递一个")
    # 根据id降序排序
    query = query.order_by("-id")
    # 获取套件执行的记录总数
    total = await query.count()
    # 分页获取数据
    data = await query.offset((page - 1) * size).limit(size).prefetch_related('suite')
    result = []
    for i in data:
        result.append({
            "id": i.id,
            "suite_id": i.suite.id,
            "suite_name": i.suite.suite_name,
            "duration": i.duration,
            "username": i.username,
            "start_time": i.start_time,
            "status": i.status,
            "run_all": i.run_all,
            "success": i.success,
            "fail": i.fail,
            "error": i.error,
            "skip": i.skip,
            "all": i.all,
            "no_run": i.no_run,
            "env": i.env,
            "suite_log": i.suite_log
        })
    return {"total": total, "data": result}


# 删除测试套件的运行记录
@router.delete('/suite/record/{record_id}', tags=['测试运行'], summary='删除套件运行记录',
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_suite_record(record_id: int):
    record = await ApiSuiteRunRecord.get_or_none(id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="套件运行记录不存在")
    await record.delete()


# 获取测试用例的运行记录
@router.get("/case/record", tags=["测试运行"], summary="用例运行记录", status_code=status.HTTP_200_OK)
async def get_case_record(case_id: int = None, suite_records_id: int = None, page: int = 1, size: int = 10):
    # 获取测试用例的运行记录
    query = ApiCaseRunRecord.all().prefetch_related('case')
    # 判断是否传了套件id
    if case_id:
        query = query.filter(case=case_id)
    elif suite_records_id:
        query = query.filter(suite_records=suite_records_id)
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="case_id和suite_records_id至少传递一个！")
    # 根据id降序排序
    query = query.order_by("-id")
    # 获取套件执行的记录总数
    total = await query.count()
    # 分页获取数据
    data = await query.offset((page - 1) * size).limit(size).prefetch_related('case')
    result = []
    for i in data:
        result.append({
            "id": i.id,
            "case_id": i.case.id,
            "case_name": i.case.case_name,
            "username": i.username,
            "start_time": i.start_time,
            "status": i.status,
            "run_info": i.run_info,
            "env": i.env,
        })
    return {"total": total, "data": result}


# 删除测试用例的运行记录
@router.delete('/case/record/{record_id}', tags=['测试运行'], summary='删除用例运行记录',
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_case_record(record_id: int):
    record = await ApiCaseRunRecord.get_or_none(id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例运行记录不存在")
    await record.delete()


# 获取单个测试用例执行结果详情
@router.get("/case/record/{record_id}", tags=["测试结果"], summary="用例的执行详情", status_code=status.HTTP_200_OK)
async def get_case_record_detail(record_id: int = None):
    # 获取测试用例的运行记录
    record = await ApiCaseRunRecord.get_or_none(id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试用例执行记录不存在！")
    # 获取测试用例的运行记录
    return record


# 获取单个测试用例执行结果详情
@router.get("/case/firstRecord/{case_id}", tags=["测试结果"], summary="用例的执行详情", status_code=status.HTTP_200_OK)
async def get_case_record_detail_for_case(case_id: int = None):
    # 获取测试用例的运行记录
    record = await ApiCaseRunRecord.filter(case_id=case_id).order_by("-id").first()
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试用例执行记录不存在！")
    # 获取测试用例的运行记录
    return record


# 获取单个测试套件执行结果详情
@router.get("/suite/record/{record_id}", tags=["测试结果"], summary="套件的执行详情", status_code=status.HTTP_200_OK,
            response_model=SuiteResultSchemas)
async def get_suite_record_detail(record_id: int):
    # 获取测试套件的运行记录
    record = await ApiSuiteRunRecord.get_or_none(id=record_id).prefetch_related('suite')
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试套件执行记录不存在！")
    result = SuiteResultSchemas(**record.__dict__, suite_name=record.suite.suite_name)
    # 获取测试套件的运行记录
    return result


# 获取单个测试计划执行结果详情
@router.get("/task/record/{record_id}", tags=["测试结果"], summary="任务的执行详情", status_code=status.HTTP_200_OK,
            response_model=TaskResultSchemas)
async def get_task_record_detail(record_id: int):
    # 获取测试套件的运行记录
    record = await ApiTaskRunRecord.get_or_none(id=record_id).prefetch_related('task')
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试计划执行记录不存在！")
    # 获取测试套件的运行记录
    result = TaskResultSchemas(**record.__dict__, task_name=record.task.name)
    return result
