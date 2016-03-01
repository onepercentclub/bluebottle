from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

app = Celery('reef',
             broker=getattr(settings, 'BROKER_URL', 'amqp://guest@localhost//'))

app.config_from_object('celeryconfig')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

celery_app = app
