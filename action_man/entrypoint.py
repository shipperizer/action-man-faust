import logging

from action_man.kafka import init_kafka
from action_man.web import init_web


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info('Initializing web application')
web = init_web()

logger.info('Bootstrap kafka application')
kafka = init_kafka()
logger.info('Bootstrap kafka application done')

logger.info('Bootstraping done')
