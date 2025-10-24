import asyncio
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from auth.auth import is_authenticated
from .schemas import DeviceSchemas
from .models import Device
from common import settings
from redis.asyncio import Redis
import json
from common.mq_producer import MQProducer

# 创建路由对象
router = APIRouter(tags=["设备管理"])


# 注册设备件
@router.post("/device", summary="注册设备", status_code=status.HTTP_201_CREATED)
async def register_device(item: DeviceSchemas):
    device = await Device.get_or_none(id=item.id)
    if device:
        device.status = "在线"
        await device.save()
        return device
    try:
        device = await Device.create(**item.model_dump())
        return device
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# 获取设备列表
@router.get("/device", summary="设备列表", status_code=status.HTTP_200_OK)
async def get_device_list(status: str = None, user_info: dict = Depends(is_authenticated)):
    query = Device.all()
    # 支持根据状态查询设备
    if status:
        query = query.filter(status=status)
    device = await query.order_by("-id")
    return device


# 获取设备详情
@router.get("/device/{device_id}", summary="设备详情", response_model=DeviceSchemas, status_code=status.HTTP_200_OK)
async def get_device_detail(device_id: str, user_info: dict = Depends(is_authenticated)):
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="设备不存在")
    return device


# 删除设备
@router.delete("/device/{device_id}", summary="删除设备", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: str, user_info: dict = Depends(is_authenticated)):
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="设备不存在")
    # 创建MQ生产者实例
    mq = MQProducer()
    try:
        # 删除消息队列device_id
        mq.channel.queue_delete(device_id)
        logging.info(f"成功删除消息队列: {device_id}")
    except Exception as e:
        logging.error(f"删除消息队列失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="设备队列清理失败！")
    finally:
        # 关闭MQ生产者实例
        mq.close()
    # 删除设备
    await device.delete()


# websocket接口
@router.websocket("/ws/{device_id}")
async def websocket_subscribe(websocket: WebSocket, device_id: str):
    await websocket.accept()
    logging.info(f"WebSocket连接已接受: {device_id}")
    redis_cli = Redis(host=settings.REDIS_CONFIG['host'],
                      port=settings.REDIS_CONFIG['port'],
                      db=settings.REDIS_CONFIG['db'],
                      password=settings.REDIS_CONFIG['password'],
                      decode_responses=True
                      )
    # 初始化一个订阅器
    pubsub = redis_cli.pubsub()
    try:
        # 订阅事件频道
        await pubsub.subscribe(f"{device_id}:log", f"{device_id}:screen")
        logging.info(f"已订阅频道：{device_id}:log 和 {device_id}:screen")
        # 发送历史日志
        history_logs = await redis_cli.lrange(f"{device_id}:history_logs", 0, -1)
        for log in history_logs:
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            message = {
                "type": "log",
                "data": log
            }
            await websocket.send_text(json.dumps(message))
            logging.info(f"发送历史日志到客户端：{log}")
        # 发送缓存画面
        msg_data = {
            "type": "log",
            "data": await redis_cli.get(f'{device_id}:cached_image')
        }
        await websocket.send_text(json.dumps(msg_data))
        # 循环接收订阅的消息
        async for message in pubsub.listen():
            # 连接断开时立即退出循环
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            if message['type'] == 'message':
                try:
                    if message['channel'] == f"{device_id}:log":
                        msg_data = {
                            "type": "log",
                            "data": message['data']
                        }
                    elif message['channel'] == f"{device_id}:screen":
                        msg_data = {
                            "type": "screen",
                            "data": message['data']
                        }
                    # 发送前最终状态确认
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_text(json.dumps(msg_data))
                        logging.info(f"发送数据到客户端: {msg_data['type']} ({len(message['data'])} 字节)")
                except RuntimeError as e:
                    if "WebSocket is not connected" in str(e):
                        break
                    logging.error(f"发送失败: {str(e)}")
                except Exception as e:
                    logging.error(f"处理消息时出错: {str(e)}")
                    break
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        logging.info(f"客户端正常断开: {device_id}")
    except Exception as e:
        logging.error(f"WebSocket处理过程中出错: {str(e)}")
    finally:
        try:
            # 连接关闭检查
            if pubsub and pubsub.subscribed:
                # 取消订阅
                await pubsub.unsubscribe()
                # 等待取消订阅完成
                await asyncio.sleep(0.1)
                logging.info(f"已取消订阅频道: {device_id}:log 和 {device_id}:screen")
        except Exception as e:
            logging.error(f"取消订阅时出错: {e}")
        if redis_cli:
            await redis_cli.close()
        if not websocket.client_state == WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except RuntimeError:
                pass
        logging.info(f"---------WebSocket连接已关闭------")
