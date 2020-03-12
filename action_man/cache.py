from os import environ

import aioredis
from aioredlock import Aioredlock, LockError


async def cache_pool() -> aioredis.ConnectionsPool:
    """ """
    return await aioredis.create_redis_pool(
        environ.get('REDIS_CNX_STRING', 'redis://redis:redis@redis:6739/0')
    )


def lock_manager() -> Aioredlock:
    ''' '''
    return Aioredlock(
        [
            environ.get('REDIS_CNX_STRING', 'redis://redis:redis@redis:6739/0')
        ]
    )


async def set_key_with_lock(
    key: str,
    value: str,
    lock_manager: Aioredlock,
    pool: aioredis.ConnectionsPool,
    execute_cmd: str = 'set'
) -> None:
    """

    :param key:
    :param value:
    :param lock_manager:
    :param pool:
    :param command:
    """
    try:
        async with await lock_manager.lock(f'lock_{key}'):
            with await pool as conn:
                command = getattr(conn, execute_cmd)
                await command(key, value)
    except LockError:
        raise
