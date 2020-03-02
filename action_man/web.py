import asyncio
from os import environ

import asyncpg
from sanic import Sanic
from sanic.response import json, stream, HTTPResponse
from sanic.request import Request

from action_man.api.actions import actions_bp
from action_man.api.demo import demo_bp
from action_man.stores.exceptions import StoreException


def init_web() -> Sanic:
    app = Sanic('action_man')

    async def setup_db(app: Sanic, loop):
        app.db_pool = await asyncpg.create_pool(
            dsn=environ.get('DB_CNX_STRING', 'postgresql://postgres:postgres@postgres:5432/actions')
        )

    async def server_error_handler(request: Request, exception: Exception) -> HTTPResponse:
        return json({'message': "Oops, server error", }, status=500)

    app.error_handler.add(StoreException, server_error_handler)

    app.register_listener(setup_db, 'before_server_start')

    app.blueprint(actions_bp)
    app.blueprint(demo_bp)

    return app
