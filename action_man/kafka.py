import base64
import collections
import logging
from os import environ
import json
from typing import Any, Dict, List

import faust
from faust.types import StreamT, TP, Message
from kafka import KafkaProducer

from action_man.monitoring import StatsdMon
from action_man import db


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class KafkaSendException(Exception):
    pass


class KafkaConnectException(Exception):
    pass


class KafkaWorker(faust.App):
    """
    Wraction_maner class for combining features of faust and Kafka-Python. The broker
    argument can be passed as a string of the form 'kafka-1:9092,kafka-2:9092'
    and the construcor will format the string as required by faust.
    """

    def __init__(self, *args: List, **kwargs: Dict) -> faust.App:
        self.broker = kwargs['broker']
        self.kafka_producer = None
        self.topics_map = {}
        kwargs['broker'] = ';'.join([f'kafka://{broker}' for broker in kwargs['broker'].split(',')])

        super().__init__(*args, **kwargs)

    def get_kafka_producer(self) -> KafkaProducer:
        """
        Return a KafkaProducer instance with sensible defaults
        """
        try:
            return KafkaProducer(
                bootstrap_servers=self.broker,
                connections_max_idle_ms=60000,
                max_in_flight_requests_per_connection=25,
                key_serializer=lambda x: x.encode() if x else None
            )
        except Exception as ex:
            raise KafkaConnectException(f'Exception while connecting to Kafka: {ex}')

    def get_topics_map(self) -> Dict:
        """
        Return map of topics
        """
        return {t.get_topic_name(): t for t in self.topics}

    def refresh_topics_map(self):
        self.topics_map = self.get_topics_map()


def init_kafka() -> KafkaWorker:
    """
    Initializing kafka action_man
    """
    logging.warning('Kafka init')
    app = KafkaWorker(
        'action_man',
        service_name='action_man',
        broker=environ.get('KAFKA_CNX_STRING', 'kafka:9092'),
        autodiscover=['action_man.actions', 'action_man.bootstrap'],
        origin='action_man',
        store=environ.get('STORE_CNX_STRING', 'memory://'),
        topic_partitions=10,
        consumer_auto_offset_reset='latest',
        web_bind='0.0.0.0',
        web_host='0.0.0.0',
        web_enabled=True,
        monitor=StatsdMon(
            host=environ.get('STATSD_HOST'),
            prefix=f'{environ.get("STATSD_PREFIX")}'
        )
    )

    logging.warning('Kafka prod init')
    app.kafka_producer = app.get_kafka_producer()

    logging.warning('Kafka topics map init')
    # refreshed every 60s due to the time the action_man takes to subscribe to topics
    app.topics_map = {}
    logging.warning('Kafka db pool init')
    # initialized after start due to async nature of object returned
    app.db_pool = None

    logging.warning('Kafka done')

    return app
