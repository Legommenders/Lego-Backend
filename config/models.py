import warnings

import django.db.utils
from diq import Dictify
from django.db import models
from smartdjango import Error, Code


@Error.register
class ConfigErrors:
    NOT_FOUND = Error("Config key not found", code=Code.NotFound)


class Config(models.Model, Dictify):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    @classmethod
    def get(cls, key):
        """Retrieve the value for a given key. Raises an error if key does not exist."""
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            raise ConfigErrors.NOT_FOUND
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
        config = cls.objects.get(key=key)
        config.delete()

    def json(self):
        """Serialize the config entry as a dictionary."""
        return self.dictify('key', 'value')
