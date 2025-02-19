from SmartDjango import Analyse
from django.views import View

from common.auth import Auth
from evaluation.models import Evaluation, Experiment, EvaluationP, ExperimentP, EvaluationError


class EvaluationView(View):
    @staticmethod
    @Analyse.r(a=[EvaluationP.signature.clone().null()])
    def get(r):
        signature = r.d.signature
        if signature:
            evaluation = Evaluation.get_by_signature(signature)
            return evaluation.json()

        return [evaluation.jsonl() for evaluation in Evaluation.objects.all()]

    @staticmethod
    @Analyse.r(b=[EvaluationP.signature, EvaluationP.command, EvaluationP.configuration])
    @Auth.require_login
    def post(r):
        evaluation = Evaluation.create_or_get(
            signature=r.d.signature,
            command=r.d.command,
            configuration=r.d.configuration,
        )
        return evaluation.json()

    @staticmethod
    @Analyse.r(a=[EvaluationP.signature])
    @Auth.require_login
    def delete(r):
        evaluation = Evaluation.get_by_signature(r.d.signature)
        evaluation.delete()


class ExperimentView(View):
    @staticmethod
    @Analyse.r(q=[
        ExperimentP.session.clone().null(),
        ExperimentP.seed.clone().null().process(int, begin=True),
        EvaluationP.signature.clone().null()
    ])
    def get(r):
        session = r.d.session
        signature, seed = r.d.signature, r.d.seed
        if session:
            experiment = Experiment.get_by_session(session)
        elif signature and seed is not None:
            evaluation = Evaluation.get_by_signature(signature)
            experiment = Experiment.create_or_get(evaluation, seed)
        else:
            raise EvaluationError.EMPTY_QUERY
        return experiment.json()

    @staticmethod
    @Analyse.r(b=[EvaluationP.signature, ExperimentP.seed])
    @Auth.require_login
    def post(r):
        evaluation = Evaluation.get_by_signature(r.d.signature)
        experiment = Experiment.create_or_get(
            evaluation=evaluation,
            seed=r.d.seed,
        )
        return experiment.session

    @staticmethod
    @Analyse.r(b=[ExperimentP.session, ExperimentP.log, ExperimentP.performance])
    @Auth.require_login
    def put(r):
        experiment = Experiment.get_by_session(r.d.session)
        experiment.complete(
            log=r.d.log,
            performance=r.d.performance,
        )
        return experiment.json()


class ExperimentRegisterView(View):
    @staticmethod
    @Analyse.r(a=[ExperimentP.session], b=[ExperimentP.pid])
    @Auth.require_login
    def post(r):
        experiment = Experiment.get_by_session(r.d.session)
        experiment.register(r.d.pid)
        return experiment.json()
