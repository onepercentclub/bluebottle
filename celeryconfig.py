from django.conf import settings


CELERY_ANNOTATIONS = {
}

CELERYBEAT_SCHEDULE = {

}

CELERY_TIMEZONE = 'Europe/Amsterdam'
CELERY_ENABLE_UTC = True
CELERY_RESULT_BACKEND = getattr(settings, 'CELERY_RESULT_BACKEND', 'amqp')
CELERY_TASK_RESULT_EXPIRES = 18000  # 5 hours.

if getattr(settings, 'CELERY_ALWAYS_EAGER', False):
    CELERY_ALWAYS_EAGER = True
