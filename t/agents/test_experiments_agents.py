import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4, uuid5, NAMESPACE_OID
from random import randint

import pytest

from action_man.experiments.agents import init_experiment, calculate_experiments
from action_man import models
from action_man import records


@pytest.mark.asyncio
async def test_init_experiment(faust, cache_pool, cache_lock_manager):
    # arrange
    experiment = records.ExperimentInit(
        experiment_id=uuid4(),
        variant_id=uuid4(),
    )

    key = f'{str(experiment.experiment_id)}_{str(experiment.variant_id)}'

    with await cache_pool as conn:
        assert not await conn.get(f'{key}_total')
        assert not await conn.get(f'{key}_successes')

    # act
    async with init_experiment.test_context() as agent:
        await agent.put(experiment)

    # assert
    with await cache_pool as conn:
        total =  await conn.get(f'{key}_total')
        successes = await conn.get(f'{key}_successes')


    assert int(total) == int(successes) == 0
    assert not await cache_lock_manager.is_locked(f'lock_{key}_successes')


@pytest.mark.xfail(reason='RuntimeError: Task <> got Future <Future pending> attached to a different loop')
@pytest.mark.asyncio
async def test_calculate_experiments_with_no_experiments_available(db_conn):
    # arrange
    assert await db_conn.fetch(f'SELECT * FROM {models.Action.__tablename__}')

    def mock_coro(return_value=None, **kwargs):
        """Create mock coroutine function."""
        async def wrapped(*args, **kwargs):
            return return_value
        return MagicMock(wraps=wrapped, **kwargs)

    # act
    with patch('action_man.experiments.agents.calculate_probabilities') as mock_calculate_prob:
        mock_calculate_prob.cast = mock_coro()
        await calculate_experiments()

    # assert
    assert mock_calculate_prob.cast.call_count == 0


@pytest.mark.xfail(reason='RuntimeError: Task <> got Future <Future pending> attached to a different loop')
@pytest.mark.asyncio
async def test_calculate_experiments_with_five_experiments_available(db_conn):
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

    def mock_coro(return_value=None, **kwargs):
        """Create mock coroutine function."""
        async def wrapped(*args, **kwargs):
            return return_value
        return MagicMock(wraps=wrapped, **kwargs)

    # take into account other saved
    record = await db_conn.fetchrow(f'SELECT count(*) as count FROM {models.Action.__tablename__}')

    # at least 5 records
    assert record.get('count') >= 5

    # act
    with patch('action_man.experiments.agents.calculate_probabilities') as mock_calculate_prob:
        mock_calculate_prob.cast = mock_coro()
        await calculate_experiments()

    # assert
    assert mock_calculate_prob.cast.call_count == record.get('count')
