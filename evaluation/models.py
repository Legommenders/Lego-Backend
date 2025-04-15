import re
from datetime import timedelta, datetime

from diq import Dictify
from django.db import models
from django.utils.crypto import get_random_string
from smartdjango import Error, Code

from common import handler
from common.space import Space


@Error.register
class EvaluationErrors:
    """Custom exception for evaluation errors."""
    EXP_NOT_FOUND = Error('Experiment not found', code=Code.NotFound)
    TAG_NOT_FOUND = Error('Tag not found', code=Code.NotFound)
    EVALUATION_NOT_FOUND = Error('Evaluation not found', code=Code.NotFound)
    EVALUATION_CREATION = Error('Evaluation creation failed', code=Code.InternalServerError)
    ALREADY_COMPLETED = Error('Experiment already completed', code=Code.BadRequest)
    EMPTY_QUERY = Error('Empty query', code=Code.BadRequest)


class Evaluation(models.Model, Dictify):
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
            raise EvaluationErrors.EVALUATION_CREATION(debug_message=e)

    @classmethod
    def create_or_get(cls, signature, command, configuration):
        """Creates or retrieves an evaluation entry."""
        try:
            evaluation = cls.objects.get(command=command)
            if evaluation.signature != signature:
                evaluation.signature = signature
                evaluation.configuration = configuration
                evaluation.save()
            return evaluation
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
            raise EvaluationErrors.EVALUATION_NOT_FOUND

    def get_tags(self):
        """Returns the tags associated with this evaluation."""
        return self.tags.all()

    def _dictify_created_at(self):
        return self.created_at.astimezone(Space.tz).isoformat()

    def _dictify_modified_at(self):
        return self.modified_at.astimezone(Space.tz).isoformat()

    def _dictify_experiments(self):
        return [exp.jsonl() for exp in self.experiment_set.all()]

    def _dictify_configuration(self):
        if self.configuration:
            return handler.json_loads(self.configuration)
        return None

    def jsonl(self):
        return self.dictify('signature', 'command', 'created_at', 'modified_at', 'comment', 'experiments')

    def json(self):
        return self.dictify('signature', 'command', 'configuration', 'created_at', 'modified_at', 'comment', 'experiments')


class Tag(models.Model, Dictify):
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
            raise EvaluationErrors.TAG_NOT_FOUND

    @classmethod
    def remove(cls, name):
        tag = cls.get_by_name(name)
        tag.delete()

    def add_evaluation(self, evaluation):
        """Associates an evaluation with the tag."""
        self.evaluations.add(evaluation)

    def _dictify_evaluations(self):
        return [evaluation.signature for evaluation in self.evaluations.all()]

    def json(self):
        """Serializes the tag model to a dictionary."""
        return self.dictify('name', 'evaluations')

    def jsonl(self):
        return self.dictify('name')


class Experiment(models.Model, Dictify):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    seed = models.IntegerField()
    session = models.CharField(max_length=32, unique=True)
    log = models.TextField(null=True, blank=True)
    performance = models.TextField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    pid = models.IntegerField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now=True)

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
            raise EvaluationErrors.EXP_NOT_FOUND

    def register(self, pid):
        self.pid = pid
        self.save()

    def complete(self, log, performance):
        """Marks the experiment as completed."""
        if self.is_completed:
            raise EvaluationErrors.ALREADY_COMPLETED
        self.log = log
        self.performance = performance
        self.is_completed = True
        self.save()

    def _dictify_created_at(self):
        return self.created_at.astimezone(Space.tz).isoformat()

    def _dictify_completed_at(self):
        return self.completed_at.astimezone(Space.tz).isoformat()

    def _dictify_signature(self):
        return self.evaluation.signature

    def _dictify_performance(self):
        if self.performance:
            return handler.json_loads(self.performance)
        return None

    def prettify_log(self):
        if self.log:
            return self.log.split('\n')
        return None

    def json(self):
        return self.dictify('signature', 'seed', 'performance', 'is_completed', 'created_at', 'completed_at', 'pid', 'summary')

    def jsonl(self):
        return self.dictify('is_completed', 'created_at', 'completed_at', 'seed', 'performance', 'pid', 'summary')

    def parse_log(self):
        if self.summary:
            return

        if not self.performance:
            return

        runtime_pattern = r'^\[(\d{2}:\d{2}:\d{2})\]'  # 匹配日志运行时间
        start_time_pattern = r'START TIME:\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)'  # 匹配绝对起始时间
        lr_line_pattern = r'\|Trainer\| use single lr:'  # 预备时间终点
        epoch_line_pattern = r'\|BaseLego\| \[epoch (\d+)\]'  # 每个 epoch 的日志行
        valid_metric_pattern = r'\|BaseLego\| \[epoch \d+\] GAUC (\d+.\d+)'  # valid set 的指标行

        def parse_runtime(s):
            h, m, sec = map(int, s.split(":"))
            return timedelta(hours=h, minutes=m, seconds=sec)

        start_time = None
        final_runtime = timedelta()
        prep_time = None
        prep_found = False

        epoch_times = []  # 存储每个 epoch 开始时间（相对）
        valid_metrics = []  # 存储 valid set 行

        lines = self.prettify_log()
        for line in lines:
            # 匹配 START TIME
            if not start_time:
                match = re.search(start_time_pattern, line)
                if match:
                    start_time = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S.%f")

            # 匹配运行时间
            runtime_match = re.search(runtime_pattern, line)
            if runtime_match:
                current_runtime = parse_runtime(runtime_match.group(1))
                final_runtime = current_runtime  # 更新最后运行时间

                # 捕获“use single lr:”之前的时间
                if not prep_found and re.search(lr_line_pattern, line):
                    prep_time = current_runtime
                    prep_found = True
                    epoch_times.append(prep_time)

                # 捕获每个 epoch 的运行时间戳
                epoch_match = re.search(epoch_line_pattern, line)
                if epoch_match:
                    epoch_times.append(current_runtime)

            # valid set 指标
            valid_match = re.search(valid_metric_pattern, line)
            if valid_match:
                valid_metrics.append(valid_match.group(1).strip())

        # 计算每个 epoch 的训练时长（用时间差）
        epoch_durations = []
        for i in range(1, len(epoch_times)):
            duration = (epoch_times[i] - epoch_times[i - 1]).total_seconds()
            epoch_durations.append(duration)

        epoch_durations = list(map(int, epoch_durations))
        valid_metrics = list(map(float, valid_metrics))

        feature = dict(
            start_time=start_time.timestamp(),
            final_time=final_runtime.total_seconds(),
            prep_time=prep_time.total_seconds(),
            total_epochs=len(epoch_times) - 1,
            epoch_durations=epoch_durations,
            valid_metrics=valid_metrics,
        )

        self.summary = handler.json_dumps(feature)
        self.save()

