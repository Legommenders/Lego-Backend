import warnings

import django.db.utils
from django.db import models
from django.core.exceptions import ValidationError


class Config(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    @classmethod
    def get(cls, key):
        """Retrieve the value for a given key. Raises an error if key does not exist."""
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            raise ValidationError(f"Config key '{key}' not found.")
        except django.db.utils.OperationalError:
            warnings.warn("Database is not ready yet. Please run migrations.")

    @classmethod
    def set(cls, key, value):
        """Set or update the value for a given key."""
        obj, created = cls.objects.update_or_create(
            key=key,
            defaults={"value": value}
        )
        return obj

    @classmethod
    def remove(cls, key):
        """Remove a config entry by key."""
        deleted_count, _ = cls.objects.filter(key=key).delete()
        if deleted_count == 0:
            raise ValidationError(f"Config key '{key}' not found.")

    def json(self):
        """Serialize the config entry as a dictionary."""
        return {
            "key": self.key,
            "value": self.value
        }
