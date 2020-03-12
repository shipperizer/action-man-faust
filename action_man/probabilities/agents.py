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


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@kafka.agent()
async def calculate_probabilities(stream: StreamT):
    """

    :param stream:

    """
    async for experiment_id in stream:
        results = {}

        db_pool = await current_agent().app.db_pool()
        cache_pool = await current_agent().app.cache_pool()
        redis_lock_manager = await current_agent().app.redis_lock_manager()

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                async for record in conn.cursor(
                    f'SELECT DISTINCT variant_id FROM {models.Action.__tablename__} WHERE experiment_id = $1',
                    experiment_id
                ):
                    variant_id = record.get('variant_id')
                    with await cache_pool as conn:
                        exp_successes = await conn.get(f'{experiment_id}_{variant_id}_successes')
                        exp_total = await conn.get(f'{experiment_id}_{variant_id}_total')
                        results[str(variant_id)] = int(exp_successes) if exp_successes is not None else 0
                        results[f'{variant_id}_total'] = int(exp_total) if exp_total is not None else 0

        calculation = {
            str(variant): ab.calculate(results[variant], results[f'{variant}_total'])
            for variant in results.keys() if not variant.endswith('_total')
        }

        calculation = json.dumps(calculation).encode('utf-8')

        await cache.set_key_with_lock(f'{experiment_id}_probabilities', calculation, redis_lock_manager, cache_pool)

        current_agent().app.kafka_producer.send('recommendation.probability', value=calculation)

        yield f'{experiment_id}_probabilities'
