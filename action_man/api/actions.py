from json import dumps

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json, HTTPResponse

from action_man.stores.actions import get_actions, save_action

actions_bp = Blueprint('actions', url_prefix='/api/actions')


@actions_bp.route('/')
async def get_action(request: Request) -> HTTPResponse:
    async with request.app.db_pool.acquire() as conn:
        actions = await get_actions(conn, limit=500)

        # intorduce Marshmallow for JSON schemas
        data = [
            {
                'id': str(action['id']),
                'session_id': str(action['session_id']),
                'reward': action['reward'],
                'context': action['context']
            }
            for action in actions
        ]

        return json(
            {
                'data': data
            }
        )


@actions_bp.route("/", methods=['POST'])
async def create_action(request: Request) -> HTTPResponse:
    # no sanitation for the time being
    data = request.json

    async with request.app.db_pool.acquire() as conn:
        action_id = await save_action(conn, data)

    return json(
        {
            'data': {
                'id': action_id
            }
        }
    )
