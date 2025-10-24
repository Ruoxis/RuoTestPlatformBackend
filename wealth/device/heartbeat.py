"""
设备心跳主动监测，检测间隔：60秒（settings.HEARTBEAT_CHECK_INTERVAL）
"""
import asyncio
import json

import aiohttp
from datetime import datetime, timedelta
from .models import Device
from common import settings
from common.redis_client import redis_cli
import logging

logger = logging.getLogger(__name__)

async def check_device_connection(device_id: str, device_ip: str) -> bool:
    """增强型设备连接检测"""
    # 方式1：HTTP健康检查（主检测方式）
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
            async with session.get(f"http://{device_ip}:{settings.DEVICE_PORT}/health") as resp:
                if resp.status == 200:
                    return True
    except:
        pass

    # 方式2：Redis心跳包检测（备用方案）
    last_heartbeat = await redis_cli.get(f"device:{device_id}:last_heartbeat")
    if last_heartbeat and datetime.now() - datetime.fromisoformat(last_heartbeat) < timedelta(seconds=30):
        return True

    return False


async def sync_device_status(device, is_alive: bool):
    """原子化状态同步操作"""
    if is_alive:
        # 心跳连接成功
        if device.status not in ["在线", "忙碌", "执行中"]:
            # 只有当状态不是"在线"或"忙碌"时才改为"在线"
            new_status = "在线"
            device.status = new_status
            await device.save(update_fields=['status'])

            # 状态变更时发布通知
            await redis_cli.publish(
                f"device:{device.id}:status",
                json.dumps({"status": new_status, "timestamp": datetime.now().isoformat()})
            )
            logger.info(f"设备状态同步 | ID:{device.id} 状态变更为:{new_status}")
    else:
        # 心跳连接失败，改为离线
        if device.status != "离线":
            new_status = "离线"
            device.status = new_status
            await device.save(update_fields=['status'])

            # 状态变更时发布通知
            await redis_cli.publish(
                f"device:{device.id}:status",
                json.dumps({"status": new_status, "timestamp": datetime.now().isoformat()})
            )
            logger.info(f"设备状态同步 | ID:{device.id} 状态变更为:{new_status}")


async def check_devices_heartbeat():
    """分布式设备心跳检测服务"""
    while True:
        try:
            # 确保获取设备时包含所有字段
            devices = await Device.all().only('id', 'ip', 'status')

            # 并行检测所有设备
            tasks = []
            for device in devices:
                task = asyncio.create_task(
                    _process_single_device(device),
                    name=f"heartbeat_check_{device.id}"
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"心跳检测主循环异常: {str(e)}", exc_info=True)

        await asyncio.sleep(settings.HEARTBEAT_CHECK_INTERVAL)  # 检测间隔

async def _process_single_device(device):
    """处理单个设备的状态检测"""
    try:
        is_alive = await check_device_connection(device.id, device.ip)
        await sync_device_status(device, is_alive)
    except Exception as e:
        logger.error(f"设备检测异常 | ID:{device.id} 错误:{str(e)}", exc_info=True)