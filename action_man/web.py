import asyncio
from os import environ

import asyncpg
from sanic import Sanic
from sanic.response import json, stream, HTTPResponse
from sanic.request import Request

from action_man import cache
from action_man import db
from action_man.api.actions import actions_bp
from action_man.api.demo import demo_bp
from action_man.stores.exceptions import StoreException


def init_web() -> Sanic:
    app = Sanic('action_man')

    async def setup_db(app: Sanic, loop):
        app.db_pool = await db.db_pool()

    async def setup_cache(app: Sanic, loop):
        app.cache_pool = await cache.cache_pool()

    async def server_error_handler(request: Request, exception: Exception) -> HTTPResponse:
        return json({'message': "Oops, server error", }, status=500)

    app.error_handler.add(StoreException, server_error_handler)

    app.register_listener(setup_cache, 'before_server_start')
    app.register_listener(setup_db, 'before_server_start')

    app.blueprint(actions_bp)
    app.blueprint(demo_bp)

    return app
