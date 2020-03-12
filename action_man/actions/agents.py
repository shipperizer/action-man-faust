import logging
import json

from faust.agents import current_agent
from faust.types import StreamT

from action_man.algorithm import ab
from action_man.entrypoint import kafka
from action_man.stores.actions import save_action
from action_man.stores.exceptions import StoreException
from action_man import cache
from action_man import models
from action_man.topics import actions_topic


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@kafka.agent(actions_topic)
async def store_actions(actions: StreamT):
    '''
    Stores actions on DB for posterous analysis.

    :param actions: StreamT:

    '''
    async for action in actions:
        logger.info(f'Storing action on db')
        db_pool = await current_agent().app.db_pool()
        async with db_pool.acquire() as conn:
            try:
                yield await save_action(conn, action.to_representation())
            except StoreException:
                logger.exception(f'Error while inserting action in DB, continuing....')
            finally:
                yield action.id


@kafka.agent(actions_topic)
async def cache_actions(actions: StreamT):
    '''
    Stores action counts on DB for posterous analysis.

    :param actions: StreamT:

    '''
    async for action in actions:
        logger.info(f'Increasing action count on cache')
        cache_pool = await current_agent().app.cache_pool()
        with await cache_pool as conn:
            await conn.incr('action_count')
            if action.reward == 1:
                await conn.incr(f'{action.experiment_id}_{action.variant_id}_successes')
            await conn.incr(f'{action.experiment_id}_{action.variant_id}_total')

        yield action.id
