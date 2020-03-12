from typing import Any

import numpy


def calculate(successes: int = 0, total: int = 0) -> Any:
    '''
    Calculate current probability based on beta distribution

    :param successes: int:  (Default value = 0)
    :param total: int:  (Default value = 0)

    '''
    return numpy.random.beta(successes + 1, total - successes + 1)
