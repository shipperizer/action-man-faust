import numpy


def calculate(successes: int=0, total: int=0):
    return numpy.random.beta(successes + 1, total - successes + 1)
