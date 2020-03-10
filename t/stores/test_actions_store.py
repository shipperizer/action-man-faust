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
async def test_get_actions_with_negative_limit_is_unused(db_conn):
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
    records = await get_actions(db_conn, experiment_id=experiment_id, limit=-100)

    # assert
    assert len(records) == 5
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
