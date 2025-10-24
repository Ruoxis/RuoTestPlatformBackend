from common.settings import *
from redis.asyncio import Redis

# 配置 Redis 连接
redis_cli = Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'],
                  db=REDIS_CONFIG['db'], password=REDIS_CONFIG['password']
                  )

