from django.conf import settings


timezone = 'Europe/Amsterdam'
enable_utc = True
result_backend = getattr(settings, 'CELERY_RESULT_BACKEND', 'rpc://')
result_serializer = 'pickle'
task_serializer = 'pickle'
accept_content = ['pickle']

task_result_expires = 18000

worker_prefetch_multiplier = 1
task_acks_late = True

if getattr(settings, 'CELERY_ALWAYS_EAGER', False):
    task_always_eager = True
    task_eager_propagates = True
    eager_propagates_exceptions = getattr(
        settings, 'CELERY_EAGER_PROPAGATES_EXCEPTIONS', True
    )
