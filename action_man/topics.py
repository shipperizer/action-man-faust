from action_man.entrypoint import kafka
from action_man.records import Action


actions_topic = kafka.topic('actions', value_type=Action)
