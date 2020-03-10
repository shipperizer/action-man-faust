import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4, uuid5, NAMESPACE_OID
from random import randint

from aioredlock import LockError
import pytest

from action_man.stores.actions import save_action, get_actions
from action_man.stores.exceptions import StoreException
from action_man.cache import set_key_with_lock, lock_manager
from action_man import records



@pytest.mark.asyncio
async def test_set_key_with_lock_with_set(cache_pool, cache_lock_manager):
    # arrange
    key = str(uuid4())

    with await cache_pool as conn:
        assert await conn.get(key) is None

    # act
    await set_key_with_lock(key, 1000, cache_lock_manager, cache_pool)

    # assert
    with await cache_pool as conn:
        assert int(await conn.get(key)) == 1000


@pytest.mark.asyncio
async def test_set_key_with_lock_with_setnx(cache_pool, cache_lock_manager):
    # arrange
    key = str(uuid4())

    with await cache_pool as conn:
        assert await conn.get(key) is None

    # act
    await set_key_with_lock(key, 1000, cache_lock_manager, cache_pool, execute_cmd='setnx')

    # assert
    with await cache_pool as conn:
        assert int(await conn.get(key)) == 1000


@pytest.mark.asyncio
async def test_set_key_with_lock_with_setnx_does_not_write_if_value_exists(cache_pool, cache_lock_manager):
    # arrange
    key = str(uuid4())

    with await cache_pool as conn:
        assert await conn.getset(key, 1000) is None

    # act
    await set_key_with_lock(key, 5000, cache_lock_manager, cache_pool, execute_cmd='setnx')

    # assert
    with await cache_pool as conn:
        assert int(await conn.get(key)) == 1000


@pytest.mark.asyncio
async def test_lock_manager_concurrent_lock_is_managed(cache_pool, cache_lock_manager):
    # arrange
    key = str(uuid4())

    # act
    lock_mgr = lock_manager()

    # assert
    async with await cache_lock_manager.lock(f'lock_{key}') as lock:
        with pytest.raises(LockError):
            await lock_mgr.lock(f'lock_{key}')


@pytest.mark.asyncio
async def test_lock_manager_locks_a_key(cache_pool):
    # arrange
    key = str(uuid4())

    # act
    lock_mgr = lock_manager()

    with pytest.raises(LockError):
        async with await lock_mgr.lock(key) as lock:
            with await cache_pool as conn:
                # assert
                assert await conn.get(key)

                # this raises
                await conn.set(key, 1000)
