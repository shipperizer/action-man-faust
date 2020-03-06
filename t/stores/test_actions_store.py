import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4, uuid5, NAMESPACE_OID
from random import randint

import pytest

from action_man.stores.actions import save_action, get_actions
from action_man.stores.exceptions import StoreException
from action_man import models
from action_man import records



@pytest.mark.asyncio
async def test_save_action_inserts_into_db(db_conn):
    # arrange
    action = records.Action(
        id=uuid4(),
        experiment_id=uuid4(),
        variant_id=uuid4(),
        reward=randint(0, 1),
        context={}
    )

    # act
    id = await save_action(db_conn, action.to_representation())

    # assert
    record = await db_conn.fetchrow(f'SELECT * FROM {models.Action.__tablename__} WHERE id = $1', id)

    assert record
    assert record.get('experiment_id') == action.experiment_id
    assert record.get('variant_id') == action.variant_id
    assert record.get('reward') == action.reward


@pytest.mark.asyncio
async def test_save_action_keeps_going_on_conflict(db_conn):
    # arrange
    action = records.Action(
        id=uuid4(),
        experiment_id=uuid4(),
        variant_id=uuid4(),
        reward=randint(0, 1),
        context={}
    )

    # act
    id = await save_action(db_conn, action.to_representation())
    assert await save_action(db_conn, action.to_representation()) == id

    # assert
    record = await db_conn.fetchrow(f'SELECT * FROM {models.Action.__tablename__} WHERE id = $1', id)

    assert record
    assert record.get('experiment_id') == action.experiment_id
    assert record.get('variant_id') == action.variant_id
    assert record.get('reward') == action.reward


@pytest.mark.asyncio
async def test_save_action_raises_if_something_is_wrong(db_conn):
    # arrange
    action = {
        'id': uuid4(),
        'experiment_id': 'fake-uuid',
        'variant_id': uuid4(),
        'reward': randint(0, 1),
        'context': [12, {}]
    }

    # act
    with pytest.raises(StoreException):
        id = await save_action(db_conn, action)

    # assert
    record = await db_conn.fetchrow(f'SELECT * FROM {models.Action.__tablename__} WHERE id = $1', action['id'])

    assert not record


@pytest.mark.asyncio
async def test_get_actions_by_experiment_id(db_conn):
    # arrange
    experiment_id = uuid4()
    actions = [
        (uuid4(), experiment_id, uuid4(), randint(0, 1), '{}')
        for i in range(5)
    ]

    await db_conn.executemany(
        f'INSERT INTO {models.Action.__tablename__} (id, experiment_id, variant_id, reward, context)'
        'VALUES ($1, $2, $3, $4, $5)',
        actions
    )

    # act
    records = await get_actions(db_conn, experiment_id=experiment_id)

    # assert
    assert len(records) == 5
    assert all([record.get('experiment_id') == experiment_id for record in records])


@pytest.mark.asyncio
async def test_get_actions_with_limit(db_conn):
    # arrange
    experiment_id = uuid4()
    actions = [
        (uuid4(), experiment_id, uuid4(), randint(0, 1), '{}')
        for i in range(5)
    ]

    await db_conn.executemany(
        f'INSERT INTO {models.Action.__tablename__} (id, experiment_id, variant_id, reward, context)'
        'VALUES ($1, $2, $3, $4, $5)',
        actions
    )

    # act
    records = await get_actions(db_conn, experiment_id=experiment_id, limit=2)

    # assert
    assert len(records) == 2
    assert all([record.get('experiment_id') == experiment_id for record in records])



@pytest.mark.asyncio
async def test_get_actions_by_id_returns_a_one_element_list(db_conn):
    # arrange
    actions = [
        (uuid4(), uuid4(), uuid4(), randint(0, 1), '{}')
        for i in range(5)
    ]

    await db_conn.executemany(
        f'INSERT INTO {models.Action.__tablename__} (id, experiment_id, variant_id, reward, context)'
        'VALUES ($1, $2, $3, $4, $5)',
        actions
    )

    # act
    records = await get_actions(db_conn, id=actions[0][0])

    # assert
    assert len(records) == 1
    assert records[0].get('id') == actions[0][0]


@pytest.mark.asyncio
async def test_get_actions_by_id_returns_empty_list(db_conn):
    # arrange
    actions = [
        (uuid4(), uuid4(), uuid4(), randint(0, 1), '{}')
        for i in range(5)
    ]

    await db_conn.executemany(
        f'INSERT INTO {models.Action.__tablename__} (id, experiment_id, variant_id, reward, context)'
        'VALUES ($1, $2, $3, $4, $5)',
        actions
    )

    # act
    records = await get_actions(db_conn, id=uuid4())

    # assert
    assert len(records) == 0


#
# @pytest.mark.asyncio
# async def test_cache_actions(faust, cache_pool):
#     # arrange
#     action = records.Action(
#         id=uuid4(),
#         experiment_id=uuid4(),
#         variant_id=uuid4(),
#         reward=randint(0, 1),
#         context={}
#     )
#
#     key = f'{str(action.experiment_id)}_{str(action.variant_id)}'
#
#     with await cache_pool as conn:
#         await conn.set(f'{key}_total', 0)
#         await conn.set(f'{key}_successes', 0)
#
#     # act
#     async with cache_actions.test_context() as agent:
#         await agent.put(action)
#
#     # assert
#     with await cache_pool as conn:
#         total =  await conn.get(f'{key}_total')
#         successes = await conn.get(f'{key}_successes')
#
#     assert int(total) == 1
#     assert int(successes) == action.reward
#
#
# @pytest.mark.asyncio
# async def test_init_experiment(faust, cache_pool, cache_lock_manager):
#     # arrange
#     experiment = records.ExperimentInit(
#         experiment_id=uuid4(),
#         variant_id=uuid4(),
#     )
#
#     key = f'{str(experiment.experiment_id)}_{str(experiment.variant_id)}'
#
#     with await cache_pool as conn:
#         assert not await conn.get(f'{key}_total')
#         assert not await conn.get(f'{key}_successes')
#
#     # act
#     async with init_experiment.test_context() as agent:
#         await agent.put(experiment)
#
#     # assert
#     with await cache_pool as conn:
#         total =  await conn.get(f'{key}_total')
#         successes = await conn.get(f'{key}_successes')
#
#
#     assert int(total) == int(successes) == 0
#     assert not await cache_lock_manager.is_locked(f'lock_{key}_successes')
#
#
# @pytest.mark.xfail(reason='RuntimeError: Task <> got Future <Future pending> attached to a different loop')
# @pytest.mark.asyncio
# async def test_calculate_experiments_with_no_experiments_available(faust, db_conn, event_loop):
#     # arrange
#     assert await db_conn.fetch(f'SELECT * FROM {models.Action.__tablename__}')
#
#     def mock_coro(return_value=None, **kwargs):
#         """Create mock coroutine function."""
#         async def wrapped(*args, **kwargs):
#             return return_value
#         return MagicMock(wraps=wrapped, **kwargs)
#
#     # act
#     with patch('action_man.actions.agents.calculate_probabilities') as mock_calculate_prob:
#         mock_calculate_prob.cast = mock_coro()
#         await calculate_experiments()
#
#     # assert
#     assert mock_calculate_prob.cast.call_count == 0
#
#
# @pytest.mark.xfail(reason='RuntimeError: Task <> got Future <Future pending> attached to a different loop')
# @pytest.mark.asyncio
# async def test_calculate_experiments_with_five_experiments_available(faust, db_conn):
#     # arrange
#     actions = [
#         (uuid4(), uuid4(), uuid4(), randint(0, 1), '{}')
#         for i in range(5)
#     ]
#
#     await db_conn.executemany(
#         f'INSERT INTO {models.Action.__tablename__} (id, experiment_id, variant_id, reward, context)'
#         'VALUES ($1, $2, $3, $4, $5)',
#         actions
#     )
#
#     def mock_coro(return_value=None, **kwargs):
#         """Create mock coroutine function."""
#         async def wrapped(*args, **kwargs):
#             return return_value
#         return MagicMock(wraps=wrapped, **kwargs)
#
#     # take into account other saved
#     record = await db_conn.fetchrow(f'SELECT count(*) as count FROM {models.Action.__tablename__}')
#
#     # at least 5 records
#     assert record.get('count') >= 5
#
#     # act
#     with patch('action_man.actions.agents.calculate_probabilities') as mock_calculate_prob:
#         mock_calculate_prob.cast = mock_coro()
#         await calculate_experiments()
#
#     # assert
#     assert mock_calculate_prob.cast.call_count == record.get('count')
#
#
# @pytest.mark.asyncio
# async def test_calculate_probabilities(faust, db_conn, cache_pool):
#     # arrange
#     experiment_id = uuid4()
#     actions = [
#         (uuid4(), experiment_id, uuid4(), randint(0, 1), '{}')
#         for i in range(5)
#     ]
#
#     await db_conn.executemany(
#         f'INSERT INTO {models.Action.__tablename__} (id, experiment_id, variant_id, reward, context)'
#         'VALUES ($1, $2, $3, $4, $5)',
#         actions
#     )
#
#
#     with await cache_pool as conn:
#         for action in actions:
#             key = f'{experiment_id}_{action[2]}'
#             await conn.set(f'{key}_total', 10)
#             await conn.set(f'{key}_successes', 5)
#
#
#     # act
#     async with calculate_probabilities.test_context() as agent:
#         await agent.put(experiment_id)
#
#     # assert
#
#     with await cache_pool as conn:
#         probabilities =  await conn.get(f'{experiment_id}_probabilities')
#
#     probabilities = json.loads(probabilities)
#
#     assert len(probabilities.values()) == 5
#
#     for value in probabilities.values():
#         assert 0 <= value <=1
