from django.core.paginator import Paginator
from django.views import View
from smartdjango import analyse, Validator, OK
from smartdjango.analyse import Request

from common.auth import Auth
from evaluation.models import Evaluation, Experiment
from evaluation.params import EvaluationParams, ExperimentParams


class EvaluationView(View):
    @analyse.argument(EvaluationParams.signature.copy().default(None, as_final=True))
    @analyse.query(
        Validator('page').default(1).to(int).to(lambda x: max(x, 1)),
        Validator('page_size').default(50).to(int).to(lambda x: min(max(x, 10), 100))
    )
    def get(self, request: Request, *args, **kwargs):
        signature = request.argument.signature
        if signature:
            evaluation = Evaluation.get_by_signature(signature)
            return evaluation.json()

        # return [evaluation.jsonl() for evaluation in Evaluation.objects.all()]
        evaluations = Evaluation.objects.all()
        paginator = Paginator(evaluations, request.query.page_size)
        page = request.query.page if request.query.page <= paginator.num_pages else paginator.num_pages
        current_page = paginator.page(page)
        return {
            'evaluations': [evaluation.jsonl() for evaluation in current_page],
            'page': page,
            'total_page': paginator.num_pages,
            'total': paginator.count,
        }

    @analyse.body(
        EvaluationParams.signature,
        EvaluationParams.command,
        EvaluationParams.configuration
    )
    @Auth.require_login
    def post(self, request: Request):
        evaluation = Evaluation.create_or_get(
            signature=request.body.signature,
            command=request.body.command,
            configuration=request.body.configuration,
        )
        return evaluation.json()

    @analyse.argument(EvaluationParams.signature)
    @Auth.require_login
    def delete(self, request: Request, **kwargs):
        evaluation = Evaluation.get_by_signature(request.argument.signature)
        evaluation.delete()
        return OK


class ExperimentView(View):
    @analyse.query(
        ExperimentParams.session.copy().default(None, as_final=True),
        ExperimentParams.seed.copy().default(None, as_final=True).to(int),
        EvaluationParams.signature.copy().default(None, as_final=True)
    )
    def get(self, request: Request):
        session = request.query.session
        signature, seed = request.query.signature, request.query.seed
        experiment = Experiment.get(signature, seed, session)
        return experiment.json()

    @analyse.body(EvaluationParams.signature, ExperimentParams.seed)
    @Auth.require_login
    def post(self, request: Request):
        evaluation = Evaluation.get_by_signature(request.body.signature)
        experiment = Experiment.create_or_get(
            evaluation=evaluation,
            seed=request.body.seed,
        )
        return experiment.session

    @analyse.body(
        ExperimentParams.session,
        ExperimentParams.log,
        ExperimentParams.performance
    )
    @Auth.require_login
    def put(self, request: Request):
        experiment = Experiment.get_by_session(request.body.session)
        experiment.complete(
            log=request.body.log,
            performance=request.body.performance,
        )
        return experiment.json()


class ExperimentRegisterView(View):
    @analyse.argument(ExperimentParams.session)
    @analyse.body(ExperimentParams.pid)
    @Auth.require_login
    def post(self, request: Request, **kwargs):
        experiment = Experiment.get_by_session(request.argument.session)
        experiment.register(request.body.pid)
        return experiment.json()


class LogView(View):
    @analyse.query(
        ExperimentParams.session.copy().default(None, as_final=True),
        ExperimentParams.seed.copy().default(None, as_final=True).to(int),
        EvaluationParams.signature.copy().default(None, as_final=True)
    )
    def get(self, request: Request):
        session = request.query.session
        signature, seed = request.query.signature, request.query.seed
        experiment = Experiment.get(signature, seed, session)
        return experiment.prettify_log()


class LogSummarizeView(View):
    def get(self, request: Request):
        for experiment in Experiment.objects.all():
            experiment.summarize()
        return OK
