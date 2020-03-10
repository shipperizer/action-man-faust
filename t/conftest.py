import asyncio
import pytest

from action_man import cache
from action_man import db
from action_man import kafka


import t.fixtures


@pytest.fixture(scope='session')
def event_loop():
    """A module-scoped event loop."""
    return asyncio.new_event_loop()

#############################################################
# DB FIXTURES
#############################################################

@pytest.fixture(scope='session')
async def db_pool(event_loop):
    yield await db.db_pool()



@pytest.fixture
async def db_conn(db_pool):
    async with db_pool.acquire() as conn:
        yield conn


#############################################################
# CACHE FIXTURES
#############################################################

@pytest.fixture(scope='session')
async def cache_pool(event_loop):
    redis = await cache.cache_pool()
    yield redis
    redis.close()
    await redis.wait_closed()

@pytest.fixture
async def cache_lock_manager(cache_pool):
    lock_manager = cache.lock_manager()
    yield lock_manager
    await lock_manager.destroy()

#############################################################
# FAUST FIXTURES
#############################################################

@pytest.fixture(scope='session')
async def faust(event_loop):
    app = kafka.init_kafka()

    app.finalize()
    app.flow_control.resume()

    yield app
