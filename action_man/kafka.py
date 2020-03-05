import asyncio
import base64
import collections
import logging
from os import environ
import json
from typing import Any, Dict, List

from asyncpg.pool import Pool
import faust
from faust.types import StreamT, TP, Message
from kafka import KafkaProducer

from action_man import cache
from action_man import db
from action_man.monitoring import StatsdMon


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class KafkaSendException(Exception):
    """ """
    pass


class KafkaConnectException(Exception):
    """ """
    pass


class KafkaWorker(faust.App):
    """Wraction_maner class for combining features of faust and Kafka-Python. The broker
    argument can be passed as a string of the form 'kafka-1:9092,kafka-2:9092'
    and the construcor will format the string as required by faust.


    """

    def __init__(self, *args: List, **kwargs: Dict) -> faust.App:
        self.broker = kwargs['broker']
        self.kafka_producer = self.get_kafka_producer()
        self.topics_map = {}
        self._db_pool = None
        self._cache_pool = None
        self._redis_lock_manager = None
        kwargs['broker'] = ';'.join([f'kafka://{broker}' for broker in kwargs['broker'].split(',')])

        super().__init__(*args, **kwargs)

    def get_kafka_producer(self) -> KafkaProducer:
        """ """
        return kafka_producer(self.broker)

    def get_topics_map(self) -> Dict:
        """ """
        return {t.get_topic_name(): t for t in self.topics}

    def refresh_topics_map(self):
        """ """
        self.topics_map = self.get_topics_map()

    async def db_pool(self) -> Pool:
        """ """
        if not self._db_pool:
            logging.warning('kafka.db_pool initialization...')
            self._db_pool = await db.db_pool()
            logging.warning('kafka.db_pool initialization...done ✓')

        return self._db_pool

    async def cache_pool(self):
        """ """
        if not self._cache_pool:
            logging.warning('kafka.cache_pool initialization...')
            self._cache_pool = await cache.cache_pool()
            logging.warning('kafka.cache_pool initialization...done ✓')

        return self._cache_pool

    async def redis_lock_manager(self):
        """ """
        if not self._redis_lock_manager:
            logging.warning('kafka.redis_lock_manager initialization...')
            self._redis_lock_manager = cache.lock_manager()
            logging.warning('kafka.redis_lock_manager initialization...done ✓')

        return self._redis_lock_manager

    async def on_stop(self) -> None:
        """ """
        if self._redis_lock_manager:
            await self._redis_lock_manager.destroy()

        if self._cache_pool:
            self._cache_pool.close()
            await self._cache_pool.wait_closed()

        await super().on_stop()


def kafka_producer(broker: str) -> KafkaProducer:
    """

    :param broker: str:
    :param broker: str:

    """
    try:
        return KafkaProducer(
            bootstrap_servers=broker,
            connections_max_idle_ms=60000,
            max_in_flight_requests_per_connection=25,
            key_serializer=lambda x: x.encode() if x else None
        )
    except Exception as ex:
        raise KafkaConnectException(f'Exception while connecting to Kafka: {ex}')


def init_kafka() -> KafkaWorker:
    """Initializing kafka action_man"""
    logging.debug('Kafka init')
    app = KafkaWorker(
        'action_man',
        service_name='action_man',
        broker=environ.get('KAFKA_CNX_STRING', 'kafka:9092'),
        autodiscover=['action_man.actions', 'action_man.bootstrap'],
        origin='action_man',
        store=environ.get('STORE_CNX_STRING', 'memory://'),
        topic_partitions=10,
        consumer_auto_offset_reset=environ.get('KAFKA_AUTO_OFFSET_RESET', 'latest'),
        web_bind='0.0.0.0',
        web_host='0.0.0.0',
        web_enabled=True,
        monitor=StatsdMon(
            host=environ.get('STATSD_HOST'),
            prefix=f'{environ.get("STATSD_PREFIX")}'
        )
    )
    logging.debug('Kafka done')

    return app
