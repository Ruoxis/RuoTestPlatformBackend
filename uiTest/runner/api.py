from fastapi import APIRouter, HTTPException, Depends, status
from wealth.device.models import Device
from wealth.environment.models import Environment
from .schemas import RunForm, SuiteResultSchemas, TaskResultSchemas
from uiTest.suite.models import Suite
from uiTest.case.models import Case
from uiTest.task.models import Task
from .models import TaskRunRecord, SuiteRunRecord, CaseRunRecord
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
        case_ = await Case.get_or_none(id=case_id)
        if not case_:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例不存在！")
        # 获取测试环境
        env = await Environment.get_or_none(id=item.env_id)
        if not env:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试环境不存在！")
        # 获取执行使用的浏览器
        browser_type = item.browser_type if item.browser_type in ["chromium", "firefox", "webkit"] else "chromium"
        # 组装执行的数据
        env_config = {
            "is_debug": item.config,
            "browser_type": browser_type,
            "host": env.host,
            "global_variable": env.global_vars
        }
        # 创建一条执行记录
        case_record = await CaseRunRecord.create(case=case_, username=item.username, env=env_config)
        run_case = {
            'id': case_.id,
            'name': case_.name,
            # 测试套件的公共前置操作
            'setup_step': [],
            "username": item.username,
            "cases": [
                {
                    "record_id": case_record.id,
                    'id': case_.id,
                    'name': case_.name,
                    "skip": False,
                    "steps": case_.steps
                }
            ]
        }
        # 获取执行的设备ID
        device_id = item.device_id
        # 判断设备的状态
        device = await Device.get_or_none(id=device_id)
        mq = MQProducer()
        if device and device.status == "在线":
            mq.send_test_task(env_config=env_config, run_case=run_case, device_id=device_id)
            mq.close()
        return {"msg": "用例执行任务已经提交到对应的设备，等待执行完毕！", "record_id": case_record.id}


# 运行测试套件
@router.post("/suite/{suite_id}", tags=["测试运行"], summary="执行套件", status_code=status.HTTP_201_CREATED)
async def run_suite(suite_id: int, item: RunForm):
    async with transactions.in_transaction():
        # 获取测试套件数据
        suite_ = await Suite.get_or_none(id=suite_id).prefetch_related('cases')
        if not suite_:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试套件不存在！")
        # 获取测试环境
        env = await Environment.get_or_none(id=item.env_id)
        if not env:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试环境不存在！")
        # 获取执行使用的浏览器
        browser_type = item.browser_type if item.browser_type in ["chromium", "firefox", "webkit"] else "chromium"
        # 组装执行的数据
        env_config = {
            "is_debug": item.config,
            "browser_type": browser_type,
            "host": env.host,
            "global_variable": env.global_vars
        }
        # 创建套件的运行记录
        suite_record = await SuiteRunRecord.create(suite=suite_, username=item.username, env=env_config)
        # 获取测试套件的用例数据
        cases = []
        for i in await suite_.cases.all().order_by("sort"):
            case_ = await i.cases
            # 创建一条执行记录
            case_record = await CaseRunRecord.create(case=case_, username=item.username, suite_records=suite_record,
                                                     env=env_config)
            cases.append({
                "record_id": case_record.id,
                'id': case_.id,
                'name': case_.name,
                "skip": i.skip,
                "steps": case_.steps
            })
        suite_record.all = len(cases)
        await suite_record.save()
        run_suite = {
            'id': suite_.id,
            'suite_record_id': suite_record.id,
            'name': suite_.name,
            'username': item.username,
            # 测试套件的公共前置操作
            'setup_step': suite_.suite_setup_step,
            "cases": cases
        }
        # 获取执行的设备ID
        device_id = item.device_id
        # 判断设备的状态
        device = await Device.get_or_none(id=device_id)
        mq = MQProducer()
        if device and device.status == "在线":
            mq.send_test_task(env_config=env_config, run_case=run_suite, device_id=device_id)
            mq.close()
        return {"msg": "套件执行任务已经提交到对应的设备，等待执行完毕！", "suite_record_id": suite_record.id}


# 运行测试计划
@router.post("/task/{task_id}", tags=["测试运行"], summary="执行任务", status_code=status.HTTP_201_CREATED)
async def run_task(task_id: int, item: RunForm):
    async with transactions.in_transaction():
        # 获取测试套件数据
        task_ = await Task.get_or_none(id=task_id).prefetch_related('suites', 'project')
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
        # 获取执行使用的浏览器
        browser_type = item.browser_type if item.browser_type in ["chromium", "firefox", "webkit"] else "chromium"
        # 组装执行的数据
        env_config = {
            "is_debug": item.config,
            "browser_type": browser_type,
            "host": env.host,
            "global_variable": env.global_vars
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
        task_record = await TaskRunRecord.create(task=task_, username=item.username, env=env_config,
                                                 project=task_.project)
        task_count = 0
        mq = MQProducer()

        # 获取测试计划的套件数据
        suites = await task_.suites.all()
        suite_case_counts = []

        # 计算每个套件的用例数量
        for suite in suites:
            suite_ = await Suite.get_or_none(id=suite.id).prefetch_related('cases')
            case_count = await suite_.cases.all().count()
            suite_case_counts.append((suite_, case_count))

        # 根据设备数量分配套件
        num_devices = len(online_device_ids)
        suites_per_device = len(suites) // num_devices
        remaining_suites = len(suites) % num_devices

        # 分配套件给设备
        device_assignments = {}
        suite_index = 0
        for i, device_id in enumerate(online_device_ids):
            # 计算分配给当前设备的套件数量
            num_suites_for_device = suites_per_device + (1 if i < remaining_suites else 0)

            device_assignments[device_id] = []
            for _ in range(num_suites_for_device):
                if suite_index < len(suite_case_counts):
                    device_assignments[device_id].append(suite_case_counts[suite_index])
                    suite_index += 1

        # 为每个设备创建任务并发送
        for device_id, assigned_suites in device_assignments.items():
            if not assigned_suites:
                continue

            # 为当前设备创建一个任务记录
            device_task_count = 0
            device_suites_data = []

            for suite_, case_count in assigned_suites:
                cases = []
                # 创建套件的运行记录
                suite_record = await SuiteRunRecord.create(suite=suite_, username=item.username, env=env_config,
                                                           task_records=task_record)

                # 获取套件中的用例数据
                for i in await suite_.cases.all().order_by("sort"):
                    case_ = await i.cases
                    # 创建一条执行记录
                    case_record = await CaseRunRecord.create(case=case_, username=item.username,
                                                             suite_records=suite_record,
                                                             env=env_config)
                    cases.append({
                        "record_id": case_record.id,
                        'id': case_.id,
                        'name': case_.name,
                        "skip": i.skip,
                        "steps": case_.steps
                    })

                device_task_count += len(cases)
                suite_record.all = len(cases)
                await suite_record.save()

                suite_data = {
                    'id': suite_.id,
                    'suite_record_id': suite_record.id,
                    'task_record_id': task_record.id,
                    'name': suite_.name,
                    "username": item.username,
                    # 测试套件的公共前置操作
                    'setup_step': suite_.suite_setup_step,
                    "cases": cases
                }
                device_suites_data.append(suite_data)

            # 发送任务到设备
            if device_suites_data:
                # 为每个套件分别发送任务
                for suite_data in device_suites_data:
                    mq.send_test_task(env_config=env_config, run_case=suite_data, device_id=device_id)

            task_count += device_task_count

        mq.close()
        # 修改任务中的用例总数
        task_record.all = task_count
        await task_record.save()
    return {"msg": f"计划执行任务已经提交到{len(online_device_ids)}个在线设备执行，等待执行完毕！",
            "task_record_id": task_record.id}


# 获取测试计划的运行记录
@router.get("/task/record", tags=["测试运行"], summary="任务运行记录", status_code=status.HTTP_200_OK)
async def get_task_record(project_id: int, task_id: int = None, page: int = 1, size: int = 10):
    # 获取测试计划的运行记录
    query = TaskRunRecord.filter(project=project_id)
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
    record = await TaskRunRecord.get_or_none(id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="任务运行记录不存在")
    await record.delete()


# 获取测试套件的运行记录
@router.get("/suite/record", tags=["测试运行"], summary="套件运行记录", status_code=status.HTTP_200_OK)
async def get_suite_record(suite_id: int = None, task_records_id: int = None, page: int = 1, size: int = 10):
    # 获取测试套件的运行记录
    query = SuiteRunRecord.all()
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
            "suite_name": i.suite.name,
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
    record = await SuiteRunRecord.get_or_none(id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="套件运行记录不存在")
    await record.delete()


# 获取测试用例的运行记录
@router.get("/case/record", tags=["测试运行"], summary="用例运行记录", status_code=status.HTTP_200_OK)
async def get_case_record(case_id: int = None, suite_records_id: int = None, page: int = 1, size: int = 10):
    # 获取测试用例的运行记录
    query = CaseRunRecord.all().prefetch_related('case')
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
            "case_name": i.case.name,
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
    record = await CaseRunRecord.get_or_none(id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例运行记录不存在")
    await record.delete()


# 获取单个测试用例执行结果详情
@router.get("/case/record/{record_id}", tags=["测试结果"], summary="用例的执行详情", status_code=status.HTTP_200_OK)
async def get_case_record_detail(record_id: int):
    # 获取测试用例的运行记录
    record = await CaseRunRecord.get_or_none(id=record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试用例执行记录不存在！")
    # 获取测试用例的运行记录
    return record


# 获取单个测试套件执行结果详情
@router.get("/suite/record/{record_id}", tags=["测试结果"], summary="套件的执行详情", status_code=status.HTTP_200_OK,
            response_model=SuiteResultSchemas)
async def get_suite_record_detail(record_id: int):
    # 获取测试套件的运行记录
    record = await SuiteRunRecord.get_or_none(id=record_id).prefetch_related('suite')
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试套件执行记录不存在！")
    result = SuiteResultSchemas(**record.__dict__, suite_name=record.suite.name)
    # 获取测试套件的运行记录
    return result


# 获取单个测试计划执行结果详情
@router.get("/task/record/{record_id}", tags=["测试结果"], summary="任务的执行详情", status_code=status.HTTP_200_OK,
            response_model=TaskResultSchemas)
async def get_task_record_detail(record_id: int):
    # 获取测试套件的运行记录
    record = await TaskRunRecord.get_or_none(id=record_id).prefetch_related('task')
    if not record:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="测试计划执行记录不存在！")
    # 获取测试套件的运行记录
    result = TaskResultSchemas(**record.__dict__, task_name=record.task.name)
    return result
