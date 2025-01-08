from django.db import models
from django.core.exceptions import ValidationError


class Evaluation(models.Model):
    signature = models.CharField(max_length=10, unique=True)
    command = models.TextField()
    configuration = models.TextField()
    log = models.TextField()
    performance = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    comment = models.TextField(blank=True)

    @classmethod
    def create_or_update(cls, signature, command, configuration, log, performance):
        """Creates or updates an evaluation entry."""
        obj, created = cls.objects.update_or_create(
            signature=signature,
            defaults={
                'command': command,
                'configuration': configuration,
                'log': log,
                'performance': performance,
            },
        )
        return obj

    @classmethod
    def remove(cls, signature):
        """Removes an evaluation entry by signature."""
        deleted_count, _ = cls.objects.filter(signature=signature).delete()
        if deleted_count == 0:
            raise ValidationError(f"Evaluation with signature '{signature}' not found.")

    def get_tags(self):
        """Returns the tags associated with this evaluation."""
        return self.tags.all()

    def json(self):
        """Serializes the evaluation model to a dictionary."""
        return {
            'signature': self.signature,
            'command': self.command,
            'configuration': self.configuration,
            'log': self.log,
            'performance': self.performance,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'comment': self.comment,
            'tags': [tag.name for tag in self.get_tags()],
        }


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    evaluations = models.ManyToManyField(Evaluation, related_name='tags')

    @classmethod
    def create_or_get(cls, name):
        """Creates or retrieves a tag by name."""
        obj, created = cls.objects.get_or_create(name=name)
        return obj

    @classmethod
    def remove(cls, name):
        """Removes a tag by name."""
        deleted_count, _ = cls.objects.filter(name=name).delete()
        if deleted_count == 0:
            raise ValidationError(f"Tag with name '{name}' not found.")

    def add_evaluation(self, evaluation):
        """Associates an evaluation with the tag."""
        self.evaluations.add(evaluation)

    def json(self):
        """Serializes the tag model to a dictionary."""
        return {
            'name': self.name,
            'evaluations': [evaluation.signature for evaluation in self.evaluations.all()],
        }
