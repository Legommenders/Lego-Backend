import re
from datetime import timedelta, datetime

import numpy as np
from diq import Dictify
from django.db import models
from django.utils.crypto import get_random_string

from common import handler, function
from common.space import Space
from evaluation.validators import EvaluationValidator, EvaluationErrors, TagValidator, ExperimentValidator


class Evaluation(models.Model, Dictify):
    vldt = EvaluationValidator

    signature = models.CharField(max_length=vldt.MAX_SIGNATURE_LENGTH, unique=True)
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
            raise EvaluationErrors.EVALUATION_CREATION(details=e)

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

    def prettify_configuration(self):
        if self.configuration:
            return handler.json_loads(self.configuration)
        return None

    def _dictify_configuration(self):
        return self.prettify_configuration()

    def prettify_performance(self, metrics=None):
        experiments = self.experiment_set.filter(is_completed=True)
        performance = dict()
        for experiment in experiments:
            current_performance = experiment.dictify_performance()
            for metric in current_performance:
                if metrics and metric.lower() not in metrics:
                    continue
                if metric not in performance:
                    performance[metric] = []
                performance[metric].append(current_performance[metric])
        for metric in performance:
            mean = np.mean(performance[metric])
            std = np.std(performance[metric], ddof=1)
            # performance[metric] = f'{mean:.4f}\\tiny' + '{' + f' ± {std:.4f}' + '}'
            performance[metric] = (mean, std)

        return performance

    def _dictify_performance(self):
        return self.prettify_performance()

    def export_rank_performance(self, metrics):
        experiments = self.experiment_set.filter(is_completed=True)
        values = []
        for experiment in experiments:
            current_performance = experiment.dictify_performance()
            current_performance = {k.lower(): v for k, v in current_performance.items()}
            for metric in metrics:
                if metric not in current_performance:
                    return 0
                values.append(current_performance[metric])
        if len(values) == 0:
            return 0
        return sum(values) / len(values)

    def _dictify_params(self):
        kwargs = function.argparse(self.command)
        data_name = kwargs['data'].split('/')[-1].split('.')[0]
        model_name = kwargs['model'].split('/')[-1].split('.')[0]
        return dict(
            data=data_name,
            model=model_name,
            batch_size=kwargs['batch_size'],
            lr=kwargs['lr'],
            lm=kwargs['lm'],
        )

    def jsonl(self):
        return self.dictify('signature', 'command', 'created_at', 'modified_at', 'comment', 'experiments')

    def json(self):
        return self.dictify('signature', 'command', 'configuration', 'created_at', 'modified_at', 'comment', 'experiments')

    def jsonl4export(self):
        return self.dictify('params', 'performance', 'command')


class Tag(models.Model, Dictify):
    vldt = TagValidator

    name = models.CharField(max_length=vldt.MAX_NAME_LENGTH, unique=True)
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
    vldt = ExperimentValidator

    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    seed = models.IntegerField()
    session = models.CharField(max_length=vldt.MAX_SESSION_LENGTH, unique=True)
    log = models.TextField(null=True, blank=True)
    performance = models.TextField(null=True, blank=True)
    pid = models.IntegerField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now=True)

    data_start_time = models.IntegerField(null=True, blank=True)
    data_final_time = models.IntegerField(null=True, blank=True)
    data_prep_time = models.IntegerField(null=True, blank=True)
    data_total_epochs = models.IntegerField(null=True, blank=True)
    data_epoch_durations = models.TextField(null=True, blank=True)
    data_valid_metrics = models.TextField(null=True, blank=True)

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

    @classmethod
    def get(cls, signature, seed, session):
        if session:
            return cls.get_by_session(session)
        elif signature and seed is not None:
            evaluation = Evaluation.get_by_signature(signature)
            return cls.create_or_get(evaluation, seed)
        raise EvaluationErrors.EMPTY_QUERY

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

        self.summarize()

    def _dictify_created_at(self):
        return self.created_at.astimezone(Space.tz).isoformat()

    def _dictify_completed_at(self):
        return self.completed_at.astimezone(Space.tz).isoformat()

    def _dictify_signature(self):
        return self.evaluation.signature

    def dictify_performance(self):
        if self.performance:
            return handler.json_loads(self.performance)
        return None

    def _dictify_performance(self):
        return self.dictify_performance()

    def _dictify_summary(self):
        return dict(
            start_time=self.data_start_time,
            final_time=self.data_final_time,
            prep_time=self.data_prep_time,
            total_epochs=self.data_total_epochs,
            epoch_durations=self.data_epoch_durations and handler.json_loads(self.data_epoch_durations),
            valid_metrics=self.data_valid_metrics and handler.json_loads(self.data_valid_metrics),
        )

    def prettify_log(self):
        if self.log:
            return self.log.split('\n')
        return None

    def json(self):
        return self.dictify('signature', 'seed', 'performance', 'is_completed', 'created_at', 'completed_at', 'pid', 'summary')

    def jsonl(self):
        return self.dictify('is_completed', 'created_at', 'completed_at', 'seed', 'performance', 'pid')

    def summarize(self):
        if not self.is_completed:
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

        self.data_start_time = start_time.timestamp()
        self.data_final_time = final_runtime.total_seconds()
        self.data_prep_time = prep_time.total_seconds()
        self.data_total_epochs = len(epoch_times) - 1
        self.data_epoch_durations = handler.json_dumps(epoch_durations)
        self.data_valid_metrics = handler.json_dumps(valid_metrics)
        self.save()
