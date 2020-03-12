from faust import Record


class Action(Record):
    ''' '''
    id: str
    experiment_id: str
    variant_id: str
    reward: int
    context: str


class ExperimentInit(Record):
    ''' '''
    experiment_id: str
    variant_id: str
