from datetime import timedelta
import logging
import json

from action_man.entrypoint import kafka
from action_man.stores.actions import save_action
from action_man.stores.exceptions import StoreException
from action_man import models
from action_man import records
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
                pass


@kafka.agent(value_type=records.Action)
async def cache_actions(actions):
    async for action in actions:
        logger.info(f'Increasing action count on cache')
        await kafka.cache_pool.incr('action_count')
        if action.reward == 1:
            await kafka.cache_pool.incr(f'{action.experiment_id}_{action.variant_id}_successes')
        await kafka.cache_pool.incr(f'{action.experiment_id}_{action.variant_id}_total')



@kafka.agent()
async def calculate_probabilities(stream):
    async for experiment_id in stream:
        results = {'total' : 0}

        async with kafka.db_pool.acquire() as conn:
            async with conn.transaction():
                async for record in conn.cursor(
                    f'SELECT DISTINCT variant_id FROM {models.Action.__tablename__} WHERE experiment_id = $1',
                    experiment_id
                ):
                    variant_id = record.get('variant_id')
                    logger.warning(f'this is the record: {record}')
                    exp_successes = await kafka.cache_pool.get(f'{experiment_id}_{variant_id}_successes')
                    exp_total = await kafka.cache_pool.get(f'{experiment_id}_{variant_id}_total')
                    results[variant_id] = int(exp_successes) if exp_successes is not None else 0
                    results['total'] += int(exp_total) if exp_total is not None else 0

        calculation = {
            str(variant): results[variant]/results['total'] if results['total'] else 0
            for variant in results.keys() if variant != 'total'
        }
        calculation = json.dumps(calculation).encode('utf-8')

        await set_key_with_lock(f'{experiment_id}_probabilities', calculation, kafka.redis_lock_manager, kafka.cache_pool)

        kafka.kafka_producer.send('recommendation.probability', value=calculation)



@kafka.timer(interval=1.0, on_leader=True)
async def calculate_experiments():
    async with kafka.db_pool.acquire() as conn:
        async with conn.transaction():
            async for record in conn.cursor(f'SELECT DISTINCT experiment_id FROM {models.Action.__tablename__}'):
                logger.warning(f'this is the record: {record}')
                await calculate_probabilities.cast(record.get('experiment_id'))



@kafka.agent(value_type=records.ExperimentInit)
async def init_experiment(experiments):
    async for experiment in experiments:
        experiment_id = experiment.experiment_id
        variant_id = experiment.variant_id

        await setnx_key_with_lock(f'{experiment_id}_{variant_id}_successes', 0, kafka.redis_lock_manager, kafka.cache_pool)
        await setnx_key_with_lock(f'{experiment_id}_{variant_id}_total', 0, kafka.redis_lock_manager, kafka.cache_pool)
        logger.info(f'Initializing {experiment_id}_{variant_id} cache keys')



async def set_key_with_lock(key, value, lock_manager, conn):
    try:
        async with await lock_manager.lock(f'lock_{key}') as lock:
            assert lock.valid is True
            await conn.set(key, value)
    except LockError:
        res = await conn.get(key)
        is_locked = await lock_manager.is_locked(key)
        logger.error(f'Lock {key} not acquired, {res} => {key} is {"locked" if is_locked else "not locked"}')
        raise


async def setnx_key_with_lock(key, value, lock_manager, conn):
    logger.warning(f'SETNX {key}={value}')
    try:
        async with await lock_manager.lock(f'lock_{key}') as lock:
            assert lock.valid is True
            await conn.setnx(key, value)
    except LockError:
        res = await conn.get(key)
        is_locked = await lock_manager.is_locked(key)
        logger.error(f'Lock {key} not acquired, {res} => {key} is {"locked" if is_locked else "not locked"}')
        raise
