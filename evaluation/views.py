from SmartDjango import Analyse
from django.views import View

from common.auth import Auth
from evaluation.models import Evaluation, Experiment, EvaluationP, ExperimentP


class EvaluationView(View):
    @staticmethod
    @Analyse.r(q=[EvaluationP.signature.clone().null()])
    def get(request):
        signature = request.d.signature
        if signature:
            evaluation = Evaluation.get_by_signature(signature)
            return evaluation.json()

        return [evaluation.json() for evaluation in Evaluation.objects.all()]

    @staticmethod
    @Analyse.r(b=[EvaluationP.signature, EvaluationP.command, EvaluationP.configuration])
    @Auth.require_login
    def post(request):
        evaluation = Evaluation.create_or_get(
            signature=request.d.signature,
            command=request.d.command,
            configuration=request.d.configuration,
        )
        return evaluation.json()

    @staticmethod
    @Analyse.r(b=[EvaluationP.signature])
    @Auth.require_login
    def delete(request):
        evaluation = Evaluation.get_by_signature(request.d.signature)
        evaluation.delete()


class ExperimentView(View):
    @staticmethod
    @Analyse.r(q=[ExperimentP.session])
    @Auth.require_login
    def get(request):
        session = request.d.session
        experiment = Experiment.get_by_session(session)
        return experiment.json()

    @staticmethod
    @Analyse.r(b=[EvaluationP.signature, ExperimentP.seed])
    @Auth.require_login
    def post(request):
        evaluation = Evaluation.get_by_signature(request.d.signature)
        experiment = Experiment.create_or_get(
            evaluation=evaluation,
            seed=request.d.seed,
        )
        return experiment.json()

    @staticmethod
    @Analyse.r(b=[ExperimentP.session, ExperimentP.log, ExperimentP.performance])
    @Auth.require_login
    def put(request):
        experiment = Experiment.get_by_session(request.d.session)
        experiment.complete(
            log=request.d.log,
            performance=request.d.performance,
        )
        return experiment.json()


class ExperimentRegisterView(View):
    @staticmethod
    @Analyse.r(a=[ExperimentP.session], b=[ExperimentP.pid])
    @Auth.require_login
    def post(request):
        experiment = Experiment.get_by_session(request.d.session)
        experiment.register(request.d.pid)
        return experiment.json()
