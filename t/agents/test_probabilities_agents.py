import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4, uuid5, NAMESPACE_OID
from random import randint

import pytest

from action_man.probabilities.agents import calculate_probabilities
from action_man import models
from action_man import records


@pytest.mark.asyncio
async def test_calculate_probabilities(faust, db_conn, cache_pool):
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


    with await cache_pool as conn:
        for action in actions:
            key = f'{experiment_id}_{action[2]}'
            await conn.set(f'{key}_total', 10)
            await conn.set(f'{key}_successes', 5)


    # act
    async with calculate_probabilities.test_context() as agent:
        await agent.put(experiment_id)

    # assert

    with await cache_pool as conn:
        probabilities =  await conn.get(f'{experiment_id}_probabilities')

    probabilities = json.loads(probabilities)

    assert len(probabilities.values()) == 5

    for value in probabilities.values():
        assert 0 <= value <=1
