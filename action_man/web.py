import asyncio
import logging
from os import environ

import asyncpg
from sanic import Sanic
from sanic.response import json, stream, HTTPResponse
from sanic.request import Request

from action_man import cache
from action_man import db
from action_man import kafka
from action_man.api.actions import actions_bp
from action_man.api.demo import demo_bp
from action_man.stores.exceptions import StoreException



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def init_web() -> Sanic:
    """ """
    app = Sanic('action_man')

    async def setup_kafka_producer(app: Sanic, loop):
        brokers = environ.get('KAFKA_CNX_STRING', 'kafka:9092')
        logger.warning(f'app.kafka initialization...{brokers}')
        app.kafka = kafka.kafka_producer(brokers)
        logger.warning('app.kafka initialized')

    async def setup_db(app: Sanic, loop):
        logger.warning('app.db_pool initialization...')
        app.db_pool = await db.db_pool()
        logger.warning('app.db_pool initialized')

    async def setup_cache(app: Sanic, loop):
        logger.warning('app.cache_pool initialization...')
        app.cache_pool = await cache.cache_pool()
        logger.warning('app.cache_pool initialized')

    async def server_error_handler(request: Request, exception: Exception) -> HTTPResponse:
        return json({'message': "Oops, server error", }, status=500)

    app.error_handler.add(StoreException, server_error_handler)

    app.register_listener(setup_cache, 'before_server_start')
    app.register_listener(setup_db, 'before_server_start')
    app.register_listener(setup_kafka_producer, 'before_server_start')

    app.blueprint(actions_bp)
    app.blueprint(demo_bp)

    return app
