from datetime import timedelta
import logging
import json

from aioredlock import LockError
from faust.agents import current_agent
from faust.types import StreamT
import numpy

from action_man.algorithm import ab
from action_man.entrypoint import kafka
from action_man.stores.actions import save_action
from action_man.stores.exceptions import StoreException
from action_man import cache
from action_man import models
from action_man import records
from action_man.topics import actions_topic
from action_man.probabilities.agents import calculate_probabilities


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@kafka.timer(interval=1.0, on_leader=True)
async def calculate_experiments():
    """
    """
    db_pool = await kafka.db_pool()

    logger.info('calculate_experiments')

    async with db_pool.acquire() as conn:
        async with conn.transaction():
            async for record in conn.cursor(f'SELECT DISTINCT experiment_id FROM {models.Action.__tablename__}'):
                await calculate_probabilities.cast(record.get('experiment_id'))


@kafka.agent(value_type=records.ExperimentInit)
async def init_experiment(experiments: StreamT):
    """

    :param experiments:

    """
    async for experiment in experiments:
        experiment_id = experiment.experiment_id
        variant_id = experiment.variant_id

        cache_pool = await kafka.cache_pool()
        redis_lock_manager = await current_agent().app.redis_lock_manager()

        await cache.set_key_with_lock(f'{experiment_id}_{variant_id}_successes', 0, redis_lock_manager, cache_pool, execute_cmd='setnx')
        await cache.set_key_with_lock(f'{experiment_id}_{variant_id}_total', 0, redis_lock_manager, cache_pool, execute_cmd='setnx')
        logger.info(f'Initializing {experiment_id}_{variant_id} cache keys')

        yield experiment_id, variant_id
