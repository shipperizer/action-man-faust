import logging
from json import dumps, loads
from random import randint, choice
from uuid import uuid4, uuid5, NAMESPACE_OID

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json, HTTPResponse


variants = [
    uuid5(NAMESPACE_OID, 'control'),
    uuid5(NAMESPACE_OID, 'test-1'),
    uuid5(NAMESPACE_OID, 'test-2')
]

demo_bp = Blueprint('demo', url_prefix='/api/demo')


@demo_bp.route('/publish', methods=['POST'])
async def publish(request: Request) -> HTTPResponse:
        probabilities = await request.app.cache_pool.get(f'{uuid5(NAMESPACE_OID, "test-experiment")}_probabilities')
        probabilities = loads(probabilities) if probabilities else  {}

        variant_id = max(probabilities.keys(), key=lambda x: probabilities[x]) if probabilities else None

        data = dumps(
            {
                'id': str(uuid4()),
                'experiment_id': str(uuid5(NAMESPACE_OID, 'test-experiment')),
                'variant_id': variant_id or str(choice(variants)),
                'reward': randint(0, 1),
                'context': '{}'
            }
        )

        data = data.encode('utf-8')

        logging.warning(f'context {request.app} {request.app.kafka}')
        request.app.kafka.send('actions', value=data)

        return json({'data': {'status': 'accepted'}})
