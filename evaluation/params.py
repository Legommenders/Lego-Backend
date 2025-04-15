from smartdjango import Params, Validator

from evaluation.models import Evaluation, Experiment


class EvaluationParams(metaclass=Params):
    model_class = Evaluation

    signature: Validator
    command: Validator
    configuration: Validator


class ExperimentParams(metaclass=Params):
    model_class = Experiment

    session: Validator
    log: Validator
    performance: Validator
    seed: Validator
    pid: Validator
