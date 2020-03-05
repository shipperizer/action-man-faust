import logging

from aioredlock import Aioredlock, LockError

from action_man.entrypoint import kafka
from action_man import cache
from action_man import db

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@kafka.task
async def create_unconsumed_topics():
    """
    Create a topic for each of the events that have no consumers yet,
    this is a one off task haction_manening at bootstrap
    """
    # ################################################ #
    # TODO: remove these once there is someone consuming the topics
    unconsumed_topics = ['dummy']

    logger.warning(
        f'Creating topics on the publisher: {unconsumed_topics} due to lack of consumers. '
        'Remove them once there are consumers'
    )
    for topic in unconsumed_topics:
        await kafka.topic(topic).maybe_declare()

    # ################################################ #


@kafka.timer(60.0)
async def refresh_topics_map():
    """
    Refresh topics_map attribute inside kafka action_man
    """
    logger.warning('Topics map refresh...')
    kafka.refresh_topics_map()
    logger.warning(kafka.topics_map)


@kafka.task
async def setnx_actions_count():
    """
    SETNX actions_count key in redis
    """
    cache_pool = await kafka.cache_pool()
    redis_lock_manager = await kafka.redis_lock_manager()

    await cache.set_key_with_lock('action_count', 0, redis_lock_manager, cache_pool, execute_cmd='setnx')
