from json import dumps
from random import random
from uuid import uuid4

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json, HTTPResponse


demo_bp = Blueprint('demo', url_prefix='/api/demo')


@demo_bp.route('/publish', methods=['POST'])
async def publish(request: Request) -> HTTPResponse:
        data = dumps(
            {
                'id': str(uuid4()),
                'session_id': str(uuid4()),
                'reward': random(),
                'context': '{}'
            }
        )

        data = data.encode('utf-8')

        request.app.kafka_producer.send('actions', value=data)

        return json({'data': {'status': 'accepted'}})
