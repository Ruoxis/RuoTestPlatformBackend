import json
import re

from fastapi import APIRouter, HTTPException, Depends, status, Body
from wealth.project.models import Project
from uiTest.runner.models import CaseRunRecord
from auth.auth import is_authenticated
from .schemas import CaseSchemas, AddCaseForm, UpdateCaseForm
from .models import Case
from zhipuai import ZhipuAI

# 创建路由对象，并指定依赖项为is_authenticated的验证，确保用户已通过身份验证
router = APIRouter(dependencies=[Depends(is_authenticated)], tags=["测试用例"])


# 创建测试用例的接口
@router.post("/case", summary="创建用例", status_code=status.HTTP_201_CREATED, response_model=CaseSchemas)
async def create_case(item: AddCaseForm):
    """创建测试用例的接口"""
    # 获取项目信息
    project = await Project.get_or_none(id=item.project_id)
    if not project:
        # 如果用例不存在，抛出错误
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="创建用例失败，传入的项目不存在")
    # 创建新的测试用例
    cases = await Case.create(**item.model_dump(exclude_unset=True))
    return cases


# 更新测试用例的接口
@router.put("/case/{case_id}", summary="更新用例", response_model=CaseSchemas, status_code=status.HTTP_200_OK)
async def update_case(case_id: int, item: UpdateCaseForm):
    """更新用例信息的接口"""
    # 获取用例信息
    cases = await Case.get_or_none(id=case_id)
    if not cases:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例不存在")
    # 更新用例信息
    await cases.update_from_dict(item.model_dump(exclude_unset=True))
    await cases.save()
    return cases


# 删除测试用例的接口
@router.delete("/case/{case_id}", summary="删除用例", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: int):
    """删除用例信息的接口"""
    cases = await Case.get_or_none(id=case_id)
    if not cases:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例不存在")
    # 删除用例
    await cases.delete()


# 获取单个用例详情的接口
@router.get("/case/{case_id}", summary="用例详情", response_model=CaseSchemas, status_code=status.HTTP_200_OK)
async def get_case_detail(case_id: int):
    """获取单个用例详情的接口"""
    cases = await Case.get_or_none(id=case_id)
    if not cases:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例不存在")
    return cases


# 复制用例
@router.post("/case/{case_id}", summary="复制用例", response_model=CaseSchemas, status_code=status.HTTP_201_CREATED)
async def copy_case(case_id: int):
    """复制用例的接口"""
    cases = await Case.get_or_none(id=case_id).prefetch_related("project")
    if not cases:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用例不存在")
    # 复制用例
    new_cases = await Case.create(name=cases.name + "_副本", project=cases.project, steps=cases.steps,
                                  level=cases.level,
                                  username=cases.username)
    return new_cases


# 查询测试用例列表
@router.get("/case", summary="用例列表", status_code=status.HTTP_200_OK)
async def get_case(project: int, page: int = 1, size: int = 10, search=None):
    """查询测试用例列表的接口"""
    # 获取所有用例
    query = Case.filter(project_id=project).order_by("-create_time")
    if search:
        query = query.filter(name__icontains=search)
    cases = await query.offset((page - 1) * size).limit(size).all()
    count = await query.count()
    # 查询用例的执行记录次数
    result = []
    for i in cases:
        run_count = await CaseRunRecord.filter(case=i).count()
        # 获取最近一次执行状态
        run_record = await CaseRunRecord.filter(case=i).order_by("-id").first()
        state = run_record.status if run_record else 'no_run'
        result.append({
            "id": i.id,
            "name": i.name,
            "username": i.username,
            "status": state,
            "run_count": run_count,
            "steps_count": len(i.steps),
            "level": i.level,
            "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "update_time": i.update_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return {"total": count, "data": result}


@router.post("/aicase", summary="AI生成用例", status_code=status.HTTP_200_OK)
async def create_aicase(username: str = Body(...),
                        module: str = Body(...),
                        demand: str = Body(...)
                        ):
    content = f"""
   你是一名专业软件测试工程师，请根据需求文档内容生成测试用例。我的需求文档内容是：{demand}
   在生成用例的时候严格遵循以下规则：
   一、字段规范（每条用例必须包含）
   1. id：顺序号（从1开始自增，示例：1, 2, 3...）  
   2. name：用例名称（概括测试场景）  
   3. module：所属模块（固定值：'{module}'）  
   4. preconditions：前置条件（系统状态/数据准备）  
   5. steps：步骤描述（带编号的明确操作，如：`1. 打开登录页\n2. 输入用户名`）  
   6. expect：预期结果（可验证的明确结果）  
   7. status：用例状态（固定值：`Prepare`）  
   8. username：责任人（固定值：'{username}'）  
   9.level：用例等级（从`P0`-`P3`中选择，P0：核心主流程，阻断性缺陷，P1：高频使用路径，重要功能，P2：次要功能/边界异常处理，P3：UI提示、文案、兼容性等低优先级场景）  
    二、生成要求
   1. 用例数量根据实际需求描述（按场景复杂度自动分配P0-P3等级）  
   2. 根据实际情况考虑，包括但不限于以下方法： 
      - 等价类划分法（有效/无效等价类） 
      - 边界值分析法（最小值、略高于/低于边界值、最大值）  
      - 场景法（覆盖基本流（正常路径）、备选流（分支路径）、异常流（错误处理））
      - 错误推测法（基于经验预测易错点，如：特殊字符、重复提交、网络中断）
   3. 步骤描述需满足：  
      - 可执行性（如明确输入值："admin' OR '1'='1"）  
      - 原子操作（每个步骤仅含1个动作）  
   4. 预期结果需：  
      - 可验证（如："显示错误码ERR-005"而非"应报错"）  
      - 包含系统响应/界面变化/数据变更  
   三、输出格式json，参考：
   [
     {{
       "id": 1,
       "name": "验证合法用户登录",
       "module": "/DIYHome4.0测试用例/8月版本用例集",
       "preconditions": "1. 已注册用户账号\\n2. 系统处于登录页",
       "steps": "1. 输入正确用户名\\n2. 输入对应密码\\n3. 点击登录按钮",
       "expect": "1. 跳转至用户主页\\n2. 显示欢迎语：用户名",
       "status": "Prepare",
       "username": "张明",
       "level": "P0"
     }},
     {{
       "id": 2,
       "name": "SQL注入攻击防御检测",
       "module": "/DIYHome4.0测试用例/8月版本用例集",
       "preconditions": "1. 系统处于登录页",
       "steps": "1. 用户名字段输入：admin' OR '1'='1\\n2. 任意密码\\n3. 点击登录",
       "expect": "1. 登录失败\\n2. 提示：安全验证未通过（ERR-114）",
       "status": "Prepare",
       "username": "张明",
       "level": "P1"
     }}
   ]
    """

    client = ZhipuAI(api_key="a92e2b06e4e80e860172480beace54a4.jdZXl2rK9saibdvB")  # 请填写您自己的APIKey
    response = client.chat.completions.create(
        model="glm-4-plus",  # 请填写您要调用的模型名称
        messages=[
            {"role": "user", "content": content},
        ],
    )
    content = response.choices[0].message.content
    pattern = r'```json\n([\s\S]*?)\n```'
    match = re.search(pattern, content)
    if not match:
        return []
    # 提取纯JSON字符串
    json_str = match.group(1)
    try:
        # 解析JSON为Python列表
        test_cases = json.loads(json_str)
        return test_cases
    except json.JSONDecodeError:
        return []
