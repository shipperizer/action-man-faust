import json
from typing import Dict, Any
import logging

import asyncpg
from asyncpg import Record, Connection

from action_man.stores.exceptions import StoreException
from action_man.models import Action


async def get_actions(conn: Connection, id: str = None, experiment_id: str = None, limit: int = 500) -> Any:
    """

    :param conn: Connection:
    :param id: str:  (Default value = None)
    :param experiment_id: str:  (Default value = None)
    :param limit: int:  (Default value = 500)

    """
    _q = [f'SELECT * FROM {Action.__tablename__}']

    if id:
        _q.append(f'WHERE id = $1')

    if experiment_id:
        _q.append(f'WHERE experiment_id = $1' if not id else f'AND WHERE experiment_id = $2')

    if limit > 0:
        _q.append(f'LIMIT {limit}')

    query = ' '.join(_q)

    q_args = [arg for arg in [id, experiment_id] if arg]

    async with conn.transaction():
        try:
            return await conn.fetch(query, *q_args)
        except asyncpg.exceptions.PostgresError as exc:
            logging.exception('Store error')
            raise StoreException from exc


async def save_action(conn: Connection, action: Dict) -> Any:
    """

    :param conn: Connection:
    :param action: Dict:

    """
    async with conn.transaction():
        try:
            await conn.execute(
                f'INSERT INTO {Action.__tablename__} (id, experiment_id, variant_id, reward, context) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING',
                action['id'], action['experiment_id'], action['variant_id'], int(action['reward']), json.dumps(action['context'])
            )
            return action['id']
        except (asyncpg.exceptions.PostgresError, asyncpg.exceptions.DataError) as exc:
            logging.exception('Store error')
            raise StoreException from exc
