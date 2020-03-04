from os import environ

import aioredis


async def cache_pool():
    return await aioredis.create_redis_pool(
        environ.get('REDIS_CNX_STRING', 'redis://redis:redis@redis:6739/0')
    )
