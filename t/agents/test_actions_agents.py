import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4, uuid5, NAMESPACE_OID
from random import randint

import pytest

from action_man.actions.agents import store_actions, cache_actions
from action_man import models
from action_man import records



@pytest.mark.asyncio
async def test_store_actions(faust, db_conn):
    # arrange
    action = records.Action(
        id=uuid4(),
        experiment_id=uuid4(),
        variant_id=uuid4(),
        reward=randint(0, 1),
        context={}
    )

    # act
    async with store_actions.test_context() as agent:
        await agent.put(action)

    # assert
    record = await db_conn.fetchrow(f'SELECT * FROM {models.Action.__tablename__} WHERE id = $1', action.id)

    assert record
    assert record.get('experiment_id') == action.experiment_id
    assert record.get('variant_id') == action.variant_id
    assert record.get('reward') in [0, 1]


@pytest.mark.asyncio
async def test_cache_actions(faust, cache_pool):
    # arrange
    action = records.Action(
        id=uuid4(),
        experiment_id=uuid4(),
        variant_id=uuid4(),
        reward=randint(0, 1),
        context={}
    )

    key = f'{str(action.experiment_id)}_{str(action.variant_id)}'

    with await cache_pool as conn:
        await conn.set(f'{key}_total', 0)
        await conn.set(f'{key}_successes', 0)

    # act
    async with cache_actions.test_context() as agent:
        await agent.put(action)

    # assert
    with await cache_pool as conn:
        total =  await conn.get(f'{key}_total')
        successes = await conn.get(f'{key}_successes')

    assert int(total) == 1
    assert int(successes) == action.reward
