from datetime import timedelta
from django.conf import settings

from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'set_status_realised': {
        'task': 'bluebottle.projects.tasks.set_status_realised',
        'schedule': crontab(minute=0, hour=0)
    },
    'update_salesforce_30': {
        'task': 'bluebottle.common.tasks.update_salesforce',
        'schedule': crontab(minute='*/30'),
        'kwargs': {
            'tenant': 'onepercent',
            'synchronize': True,
            'updated': 60,
            'log_to_salesforce': True
        }
    },
    'update_salesforce_week': {
        'task': 'bluebottle.common.tasks.update_salesforce',
        'schedule': crontab(minute=0, hour=12, day_of_week='sun'),
        'kwargs': {
            'tenant': 'onepercent',
            'csv_export': True,
            'log_to_salesforce': True
        }
    },
    'update-popularity': {
        'task': 'bluebottle.projects.tasks.update_popularity',
        'schedule': timedelta(hours=1),
    },
    'sync-surveys': {
        'task': 'bluebottle.surveys.tasks.sync_surveys',
        'schedule': timedelta(hours=1),
    },
}

CELERY_TIMEZONE = 'Europe/Amsterdam'
CELERY_ENABLE_UTC = True
CELERY_RESULT_BACKEND = getattr(settings, 'CELERY_RESULT_BACKEND', 'amqp')
CELERY_TASK_RESULT_EXPIRES = 18000  # 5 hours.

if getattr(settings, 'CELERY_ALWAYS_EAGER', False):
    CELERY_ALWAYS_EAGER = True
