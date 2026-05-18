from django.conf import settings


timezone = 'Europe/Amsterdam'
enable_utc = True
result_backend = getattr(settings, 'CELERY_RESULT_BACKEND', 'rpc://')
result_serializer = 'pickle'
task_serializer = 'pickle'
accept_content = ['pickle']

task_result_expires = 18000

if getattr(settings, 'CELERY_ALWAYS_EAGER', False):
    always_eager = True
