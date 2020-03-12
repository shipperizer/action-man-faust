from asyncio import AbstractEventLoop
import logging
from os import environ
from typing import Dict, List

from asyncpg.pool import Pool
from aioredis import ConnectionsPool
from aioredlock import Aioredlock
import faust
from kafka import KafkaProducer

from action_man import cache
from action_man import db
from action_man.monitoring import StatsdMon


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class KafkaConnectException(Exception):
    pass


class KafkaWorker(faust.App):
    '''Wraction_maner class for combining features of faust and Kafka-Python. The broker
    argument can be passed as a string of the form 'kafka-1:9092,kafka-2:9092'
    and the construcor will format the string as required by faust.


    '''

    def __init__(self, *args: List, **kwargs: Dict) -> None:
        self.broker : str = kwargs.pop('broker')
        self.topics_map : Dict[str, faust.agents.Agent] = {}

        logging.warning('kafka.kafka_producer initialization...')
        self._kafka_producer = get_kafka_producer(self.broker)
        logging.warning('kafka.kafka_producer initialization...done ✓')

        self._db_pool = None
        self._cache_pool = None
        self._redis_lock_manager = None

        super().__init__(*args, broker=KafkaWorker._broker_faust_string(self.broker), **kwargs)

    @staticmethod
    def _broker_faust_string(cnx_string: str) -> str:
        return ';'.join([f'kafka://{broker}' for broker in cnx_string.split(',')])

    def get_topics_map(self) -> Dict:
        ''' '''
        return {t.get_topic_name(): t for t in self.topics}

    def refresh_topics_map(self) -> None:
        ''' '''
        self.topics_map = self.get_topics_map()

    async def db_pool(self) -> Pool:
        """ """
        if not self._db_pool:
            logging.warning('kafka.db_pool initialization...')
            self._db_pool = await db.db_pool()
            logging.warning('kafka.db_pool initialization...done ✓')

        return self._db_pool

    async def cache_pool(self) -> ConnectionsPool:
        """ """
        if not self._cache_pool:
            logging.warning('kafka.cache_pool initialization...')
            self._cache_pool = await cache.cache_pool()
            logging.warning('kafka.cache_pool initialization...done ✓')

        return self._cache_pool

    async def redis_lock_manager(self) -> Aioredlock:
        """ """
        if not self._redis_lock_manager:
            logging.warning('kafka.redis_lock_manager initialization...')
            self._redis_lock_manager = cache.lock_manager()
            logging.warning('kafka.redis_lock_manager initialization...done ✓')

        return self._redis_lock_manager

    def kafka_producer(self) -> KafkaProducer:
        """ """
        return self._kafka_producer

    async def on_stop(self) -> None:
        """ """
        if self._redis_lock_manager:
            await self._redis_lock_manager.destroy()

        if self._cache_pool:
            self._cache_pool.close()
            await self._cache_pool.wait_closed()

        await super().on_stop()


def get_kafka_producer(broker: str) -> KafkaProducer:
    '''

    :param broker: str:

    '''
    try:
        return KafkaProducer(
            bootstrap_servers=broker,
            connections_max_idle_ms=10000,
            key_serializer=lambda x: x.encode() if x else None
        )
    except Exception as exc:
        raise KafkaConnectException(f'Exception while connecting to Kafka: {exc}') from exc



def init_kafka() -> KafkaWorker:
    '''Initializing kafka action_man'''
    logging.debug('Kafka init')
    app = KafkaWorker(
        'action_man',
        service_name='action_man',
        broker=environ.get('KAFKA_CNX_STRING', 'kafka:9092'),
        autodiscover=[
            'action_man.actions', 'action_man.bootstrap', 'action_man.experiments', 'action_man.probabilities'
        ],
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
