from __future__ import absolute_import

from celery import Celery
from django.conf import settings

app = Celery('bluebottle', broker=getattr(settings, 'BROKER_URL', 'amqp://guest@localhost//'))

app.config_from_object('celeryconfig')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
