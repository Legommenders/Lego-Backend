# ignore_security_alert_file SQL_INJECTION
from django.core.paginator import Paginator
from django.views import View
from smartdjango import analyse, Validator, OK
from smartdjango.analyse import Request

from common import auth
from evaluation.export import get_top_rank_models_per_datasets, get_total_running_hours
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

    @analyse.json(
        EvaluationParams.signature,
        EvaluationParams.command,
        EvaluationParams.configuration
    )
    @auth.require_login
    def post(self, request: Request):
        evaluation = Evaluation.create_or_get(
            signature=request.json.signature,
            command=request.json.command,
            configuration=request.json.configuration,
        )
        return evaluation.json()

    @analyse.argument(EvaluationParams.signature)
    @auth.require_login
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
    def get(self, request: Request, **kwargs):
        session = request.query.session
        signature, seed = request.query.signature, request.query.seed
        experiment = Experiment.get(signature, seed, session)
        return experiment.json()

    @analyse.json(EvaluationParams.signature, ExperimentParams.seed)
    @auth.require_login
    def post(self, request: Request):
        evaluation = Evaluation.get_by_signature(request.json.signature)
        experiment = Experiment.create_or_get(
            evaluation=evaluation,
            seed=request.json.seed,
        )
        return experiment.session

    @analyse.json(
        ExperimentParams.session,
        ExperimentParams.log,
        ExperimentParams.performance
    )
    @auth.require_login
    def put(self, request: Request):
        experiment = Experiment.get_by_session(request.json.session)
        experiment.complete(
            log=request.json.log,
            performance=request.json.performance,
        )
        return experiment.json()


class ExperimentRegisterView(View):
    @analyse.argument(ExperimentParams.session)
    @analyse.json(ExperimentParams.pid)
    @auth.require_login
    def post(self, request: Request, **kwargs):
        experiment = Experiment.get_by_session(request.argument.session)
        experiment.register(request.json.pid)
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


class ExportView(View):
    @analyse.query(
        Validator('replicate').default(5, as_final=True),
        Validator('metrics').default(None, as_final=True).to(lambda x: x.split(',')),
        Validator('datasets').default(None, as_final=True).to(lambda x: x.split(',')),
        Validator('scenario').default('get_top_rank_models_per_datasets', as_final=True),
        Validator('top_k').default(1, as_final=True).to(int),
        Validator('return_table').default(0, as_final=True).to(int),
    )
    def get(self, request: Request):
        replicate = request.query.replicate
        metrics = request.query.metrics()
        datasets = request.query.datasets()

        scenario = request.query.scenario
        if scenario == 'get_top_rank_models_per_datasets':
            return get_top_rank_models_per_datasets(replicate, metrics, datasets, top_k=request.query.top_k, return_table=request.query.return_table)
        if scenario == 'get_total_running_hours':
            return get_total_running_hours()

        return OK

        # selected_evaluations = []
        # for evaluation in Evaluation.objects.all():
        #     experiments = Experiment.objects.filter(evaluation=evaluation, is_completed=True)
        #     if experiments.count() >= replicate:
        #         selected_evaluations.append(evaluation)
        #
        # evaluations = [evaluation.jsonl4export() for evaluation in selected_evaluations]
        #
        # models = ['dnn', 'pnn', 'deepfm', 'dcn', 'dcnv2', 'din', 'autoint', 'finalmlp', 'gdcn', 'masknet']
        # pretty_models = {
        #     'dnn': 'DNN',
        #     'pnn': 'PNN',
        #     'deepfm': 'DeepFM',
        #     'dcn': 'DCN',
        #     'dcnv2': 'DCNv2',
        #     'din': 'DIN',
        #     'autoint': 'AutoInt',
        #     'finalmlp': 'FinalMLP',
        #     'gdcn': 'GDCN',
        #     'masknet': 'MaskNet',
        # }
        # use_id = True
        #
        # if use_id:
        #     models = [f'{method}_id' for method in models]
        #
        # datasets = ['automotive', 'books', 'cds']
        # metrics = ['gauc', 'mrr', 'ndcg@1']
        #
        # table = dict()
        #
        # for model in models:
        #     table[model] = dict()
        #     for dataset in datasets:
        #         table[model][dataset] = dict()
        #
        # for evaluation in evaluations:
        #     model_name = evaluation['params']['model'].lower()
        #     data_name = evaluation['params']['data'].lower()
        #     performance = {k.lower(): v for k, v in evaluation['performance'].items()}
        #
        #     if model_name in models and data_name in datasets:
        #         for metric in metrics:
        #             table[model_name][data_name][metric] = performance[metric]
        #
        # lines = []
        # for model in models:
        #     model_name = model.split('_id')[0] if use_id else model
        #     model_name = pretty_models[model_name]
        #     if use_id:
        #         model_name = f'{model_name}' + '$_\\text{ID}$'
        #     elements = [model_name]
        #
        #     for dataset in datasets:
        #         for metric in metrics:
        #             elements.append(table[model][dataset].get(metric, ''))
        #     string = ' & '.join(elements) + ' \\\\'
        #     lines.append(string)
        #
        # return '\n'.join(lines)
