from SmartDjango import Analyse
from SmartDjango.p import P
from django.views import View

from common.auth import Auth
from evaluation.models import Evaluation, Experiment


class EvaluationView(View):
    @staticmethod
    @Analyse.r(q=[P('signature').set_null()])
    def get(r):
        signature = r.d.signature
        if signature:
            evaluation = Evaluation.get_by_signature(signature)
            return evaluation.json()

        return [evaluation.json() for evaluation in Evaluation.objects.all()]

    @staticmethod
    @Analyse.r(b=['signature', 'command', 'configuration', 'seed'])
    @Auth.require_login
    def post(r):
        evaluation = Evaluation.create_or_get(
            signature=r.d.signature,
            command=r.d.command,
            configuration=r.d.configuration,
        )
        experiment = Experiment.create_or_get(
            evaluation=evaluation,
            seed=r.d.seed,
        )
        return experiment.session

    @staticmethod
    @Analyse.r(b=['session', 'log', 'performance'])
    @Auth.require_login
    def put(r):
        experiment = Experiment.get_by_session(r.d.session)
        experiment.complete(
            log=r.d.log,
            performance=r.d.performance,
        )
        return experiment.json()

    @staticmethod
    @Analyse.r(b=['signature'])
    @Auth.require_login
    def delete(r):
        evaluation = Evaluation.get_by_signature(r.d.signature)
        evaluation.delete()
