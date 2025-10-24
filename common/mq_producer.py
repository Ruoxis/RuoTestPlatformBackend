import pika
import json
import time
from .settings import MQ_CONFIG
from pika.exceptions import AMQPConnectionError
from typing import Dict, Any


class MQProducer:
    """
    MQ消息生产者
    支持UI测试和API测试两种模式

    Attributes:
        is_api: 是否为API测试模式
        exchange_name: API测试专用交换机名称
    """

    def __init__(self, is_api=False):
        self.connection = None
        self.channel = None
        self.is_api = is_api
        self.exchange_name = MQ_CONFIG.get('api_exchange', 'api_test_exchange') if is_api else ''
        self.reconnect()

    def reconnect(self):
        """
        尝试重新连接到RabbitMQ服务器
        """
        while True:
            try:
                # 连接到RabbitMQ服务器
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=MQ_CONFIG.get('host'), port=MQ_CONFIG.get('port'),
                        credentials=pika.credentials.PlainCredentials(username=MQ_CONFIG.get('username'),
                                                                      password=MQ_CONFIG.get('password')),
                        # 设置心跳检测
                        heartbeat=MQ_CONFIG.get('heartbeat', 600),
                        # 设置阻塞连接超时时间
                        blocked_connection_timeout=MQ_CONFIG.get('blocked_connection_timeout', 300),
                        # 尝试连接的次数
                        connection_attempts=3,
                        # 重试连接的延迟时间（秒）
                        retry_delay=5)
                )
                # 创建一个通道
                self.channel = self.connection.channel()
                print("mq连接成功")
                # 连接成功，退出循环
                break
            except pika.exceptions.AMQPConnectionError as e:
                print(f"连接错误 {e}，等待5秒后重新连接...")
                # 等待5秒后重试连接
                time.sleep(5)
            except Exception as e:
                print(f"API测试MQ连接失败: {e}, 5秒后重试...")
                time.sleep(5)

    def _check_connection(self):
        """
        检查连接状态，必要时重新连接

        Returns:
            bool: 连接是否有效
        """
        if (self.connection is None or self.connection.is_closed or
                self.channel is None or self.channel.is_closed):
            print("MQ连接已断开，尝试重新连接...")
            return self.reconnect()
        return True

    def send_test_task(self, env_config, run_case, device_id):
        """
        :param env_config: 运行用例的环境数据
        :param run_case: 运行用例的套件数据
        :param device_id: 指定执行的设备
        :return:
        """
        data = {
            'env_config': env_config,
            'run_suite': run_case
        }
        message = json.dumps(data, ensure_ascii=False).encode('utf-8')
        if self.connection is None or self.channel is None or self.connection.is_closed or self.channel.is_closed:
            # 重新连接
            self.reconnect()
        # 连接到通道
        self.channel = self.connection.channel()
        # 声明队列device_id
        self.channel.queue_declare(queue=device_id, durable=True)
        # 提交消息到队列device_id中

        self.channel.basic_publish(exchange='', routing_key=device_id, body=message,
                                   properties=pika.BasicProperties(
                                       delivery_mode=2,  # 持久化消息
                                       content_type='application/json',
                                       headers={'task_type': 'ui_test'}  # 明确标识任务类型
                                   ))

    def send_api_test_task(self, env_config, run_case, device_id: str):
        """
        :param env_config: 运行用例的环境数据
        :param run_case: 运行用例的套件数据
        :param device_id: 指定执行的设备
        :return:
        """
        try:
            if not self._check_connection():
                raise Exception("MQ连接不可用，无法发送消息")

            message = json.dumps({'env_config': env_config, 'run_suite': run_case}, ensure_ascii=False).encode('utf-8')
            # 发布消息到API测试交换机，使用设备ID作为路由键
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=device_id,  # 使用设备ID进行路由
                body=message,
                properties=pika.BasicProperties(delivery_mode=2,  # 持久化消息
                                                content_type='application/json',
                                                headers={'task_type': 'api_test'}  # 标记为API测试任务
                                                ))

            print(f"API测试任务已发送到设备 {device_id}")

        except Exception as e:
            print(f"发送API测试任务失败: {e}")
            self.reconnect()
            raise

    def close(self):
        """关闭mq对象"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("API测试MQ生产者连接已关闭")
