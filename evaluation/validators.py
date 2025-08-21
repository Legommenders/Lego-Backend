from smartdjango import Error, Code


@Error.register
class EvaluationErrors:
    """Custom exception for evaluation errors."""
    EXP_NOT_FOUND = Error('Experiment not found', code=Code.NotFound)
    TAG_NOT_FOUND = Error('Tag not found', code=Code.NotFound)
    EVALUATION_NOT_FOUND = Error('Evaluation not found', code=Code.NotFound)
    EVALUATION_CREATION = Error('Evaluation creation failed', code=Code.InternalServerError)
    ALREADY_COMPLETED = Error('Experiment already completed', code=Code.BadRequest)
    EMPTY_QUERY = Error('Empty query', code=Code.BadRequest)


class EvaluationValidator:
    MAX_SIGNATURE_LENGTH = 10


class TagValidator:
    MAX_NAME_LENGTH = 50


class ExperimentValidator:
    MAX_SESSION_LENGTH = 32
