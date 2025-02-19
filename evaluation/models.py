from SmartDjango import E, Hc, models
from django.utils.crypto import get_random_string

from common import handler


class EvaluationError:
    """Custom exception for evaluation errors."""
    EXP_NOT_FOUND = E('Experiment not found', hc=Hc.NotFound)
    TAG_NOT_FOUND = E('Tag not found', hc=Hc.NotFound)
    EVALUATION_NOT_FOUND = E('Evaluation not found', hc=Hc.NotFound)
    EVALUATION_CREATION = E('Evaluation creation failed', hc=Hc.InternalServerError)
    ALREADY_COMPLETED = E('Experiment already completed', hc=Hc.BadRequest)


class Evaluation(models.Model):
    signature = models.CharField(max_length=10, unique=True)
    command = models.TextField(unique=True)
    configuration = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    comment = models.TextField(blank=True)

    @classmethod
    def create(cls, signature, command, configuration):
        """Creates or updates an evaluation entry."""
        try:
            return cls.objects.create(
                signature=signature,
                command=command,
                configuration=configuration,
            )
        except Exception as e:
            raise EvaluationError.EVALUATION_CREATION(debug_message=e)

    @classmethod
    def create_or_get(cls, signature, command, configuration):
        """Creates or retrieves an evaluation entry."""
        try:
            return cls.objects.get(signature=signature)
        except cls.DoesNotExist:
            return cls.create(
                signature=signature,
                command=command,
                configuration=configuration,
            )

    @classmethod
    def exist_by_signature(cls, signature):
        """Check if an evaluation entry exists by signature."""
        return cls.objects.filter(signature=signature).exists()

    @classmethod
    def get_by_signature(cls, signature):
        """Retrieves an evaluation entry by signature."""
        try:
            return cls.objects.get(signature=signature)
        except cls.DoesNotExist:
            raise EvaluationError.EVALUATION_NOT_FOUND

    def get_tags(self):
        """Returns the tags associated with this evaluation."""
        return self.tags.all()

    def _readable_created_at(self):
        return self.created_at.isoformat()

    def _readable_modified_at(self):
        return self.modified_at.isoformat()

    def _readable_experiments(self):
        return [exp.jsonl() for exp in self.experiment_set.all()]

    def _readable_configuration(self):
        return handler.json_loads(self.configuration)

    def json(self):
        return self.dictify('signature', 'command', 'configuration', 'created_at', 'modified_at', 'comment', 'experiments')


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    evaluations = models.ManyToManyField(Evaluation, related_name='tags')

    @classmethod
    def create_or_get(cls, name):
        """Creates or retrieves a tag by name."""
        obj, created = cls.objects.get_or_create(name=name)
        return obj

    @classmethod
    def get_by_name(cls, name):
        """Retrieves a tag by name."""
        try:
            return cls.objects.get(name=name)
        except cls.DoesNotExist:
            raise EvaluationError.TAG_NOT_FOUND

    @classmethod
    def remove(cls, name):
        tag = cls.get_by_name(name)
        tag.delete()

    def add_evaluation(self, evaluation):
        """Associates an evaluation with the tag."""
        self.evaluations.add(evaluation)

    def _readable_evaluations(self):
        return [evaluation.signature for evaluation in self.evaluations.all()]

    def json(self):
        """Serializes the tag model to a dictionary."""
        return self.dictify('name', 'evaluations')

    def jsonl(self):
        return self.dictify('name')


class Experiment(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    seed = models.IntegerField()
    session = models.CharField(max_length=32, unique=True)
    log = models.TextField(null=True, blank=True)
    performance = models.TextField(null=True, blank=True)
    pid = models.IntegerField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create(cls, evaluation, seed):
        exp = cls.objects.create(
            evaluation=evaluation,
            seed=seed,
            session=get_random_string(length=32),
        )
        return exp

    @classmethod
    def create_or_get(cls, evaluation, seed):
        try:
            return cls.objects.get(evaluation=evaluation, seed=seed)
        except cls.DoesNotExist:
            return cls.create(evaluation, seed)

    @classmethod
    def get_by_session(cls, session):
        """Retrieves an experiment by session."""
        try:
            return cls.objects.get(session=session)
        except cls.DoesNotExist:
            raise EvaluationError.EXP_NOT_FOUND

    def register(self, pid):
        self.pid = pid
        self.save()

    def complete(self, log, performance):
        """Marks the experiment as completed."""
        if self.is_completed:
            raise EvaluationError.ALREADY_COMPLETED
        self.log = log
        self.performance = performance
        self.is_completed = True
        self.save()

    def _readable_created_at(self):
        return self.created_at.isoformat()

    def _readable_signature(self):
        return self.evaluation.signature

    def json(self):
        return self.dictify('signature', 'seed', 'session', 'log', 'performance', 'is_completed', 'created_at', 'registered_pid')

    def jsonl(self):
        return self.dictify('session', 'is_completed', 'created_at', 'seed', 'performance')


class EvaluationP:
    try:
        signature, command, configuration = Evaluation.get_params(
            'signature', 'command', 'configuration')
    except Exception:
        print('error occurs in finding evaluation params')
        signature, command, configuration = None, None, None


class ExperimentP:
    try:
        session, log, performance, seed, pid = Experiment.get_params(
            'session', 'log', 'performance', 'seed', 'pid')
    except Exception:
        print('error occurs in finding experiment params')
        session, log, performance, seed, pid = None, None, None, None, None
