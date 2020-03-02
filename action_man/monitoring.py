import base64
import collections
import logging
from os import environ
import json
from typing import Any

from faust.sensors.monitor import Monitor
from faust.sensors.statsd import StatsdMonitor
from faust.types import StreamT, TP, Message


class StatsdMon(StatsdMonitor):
    """ """
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 8125,
        prefix: str = 'x.faust',
        rate: float = 1.0,
        **kwargs: Any
    ) -> None:
        super().__init__(host=host, port=port, prefix=f'{prefix}.faust', rate=rate, **kwargs)

    def _stream_label(self, stream: StreamT) -> str:
        """
        Enhance original _stream_label function
        it converts "topic_foo-bar.data" -> "foo-bar_data"

        :param stream: StreamT:
        :param stream: StreamT:

        """
        label = super()._stream_label(stream=stream)
        return label.replace('topic_', '').replace('.', '_')

    def on_message_in(self, tp: TP, offset: int, message: Message) -> None:
        """Call before message is delegated to streams.

        :param tp: TP:
        :param offset: int:
        :param message: Message:
        :param tp: TP:
        :param offset: int:
        :param message: Message:

        """
        super(Monitor, self).on_message_in(tp, offset, message)

        topic = tp.topic.replace('.', '_')
        self.client.incr('messages_received', rate=self.rate)
        self.client.incr('messages_active', rate=self.rate)
        self.client.incr(f'topic.{topic}.messages_received', rate=self.rate)
        self.client.gauge(f'read_offset.{topic}.{tp.partition}', offset)
