import pytz

from backend import settings
from config.models import Config


class Space:
    auth = Config.get('auth')
    tz = pytz.timezone(settings.TIME_ZONE)

