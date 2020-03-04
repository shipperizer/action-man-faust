from datetime import timedelta
import logging

from action_man.entrypoint import kafka
from action_man.stores.actions import save_action
from action_man.stores.exceptions import StoreException
from action_man.topics import actions_topic


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@kafka.agent(actions_topic)
async def store_actions(actions):
    """
    Stores actions on DB for posterous analysis.
    Processed in batches of up to 1000
    """
    async for action in actions:
        logger.info(f'Storing action on db')
        await cache_actions.cast(action)
        async with kafka.db_pool.acquire() as conn:
                try:
                    await save_action(conn, action.to_representation())
                except StoreException:
                    logger.exception(f'Error while inserting action in DB, continuing....')
                    continue


@kafka.agent
async def cache_actions(actions):
    async for action in actions:
        logger.info(f'Increasing action count on cache')
        await kafka.cache_pool.incr('action_count')
