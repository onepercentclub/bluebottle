from django.conf import settings


timezone = 'Europe/Amsterdam'
enable_utc = True
result_backend = getattr(settings, 'CELERY_RESULT_BACKEND', 'rpc://')
result_serializer = 'pickle'
task_serializer = 'pickle'
accept_content = ['pickle']

task_result_expires = 18000

if getattr(settings, 'CELERY_ALWAYS_EAGER', False):
    # Celery 5+ uses task_always_eager; always_eager is ignored.
    task_always_eager = True
    task_eager_propagates = getattr(
        settings, 'CELERY_EAGER_PROPAGATES_EXCEPTIONS', False
    )
