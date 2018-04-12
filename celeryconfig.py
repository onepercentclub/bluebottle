from datetime import timedelta

from celery.schedules import crontab
from django.conf import settings


CELERY_ANNOTATIONS = {
    'bluebottle.analytics.tasks.queue_analytics_record': {'rate_limit': '50/s'}
}

CELERYBEAT_SCHEDULE = {
    'generate_engagement_metrics': {
        'task': 'bluebottle.analytics.tasks.generate_engagement_metrics',
        'schedule': crontab(minute='*/30')
    },
    'set_status_realised': {
        'task': 'bluebottle.projects.tasks.set_status_realised',
        'schedule': crontab(minute=0, hour=0)
    },
    'update_popularity': {
        'task': 'bluebottle.projects.tasks.update_popularity',
        'schedule': timedelta(hours=1),
    },
    'update_exchange_rates': {
        'task': 'bluebottle.projects.tasks.update_exchange_rates',
        'schedule': crontab(minute=1, hour=3),
    },
    'update_project_status_stats': {
        'task': 'bluebottle.projects.tasks.update_project_status_stats',
        'schedule': crontab(hour=0, minute=0),
    },
    'task_reminder_mails': {
        'task': 'bluebottle.tasks.tasks.send_task_reminder_mails',
        'schedule': crontab(hour=9, minute=30),
    },
    'sync_surveys': {
        'task': 'bluebottle.surveys.tasks.sync_surveys',
        'schedule': timedelta(hours=1),
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
}

CELERY_TIMEZONE = 'Europe/Amsterdam'
CELERY_ENABLE_UTC = True
CELERY_RESULT_BACKEND = getattr(settings, 'CELERY_RESULT_BACKEND', 'amqp')
CELERY_TASK_RESULT_EXPIRES = 18000  # 5 hours.

if getattr(settings, 'CELERY_ALWAYS_EAGER', False):
    CELERY_ALWAYS_EAGER = True
