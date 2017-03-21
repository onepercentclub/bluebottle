from django.conf import settings

from .tasks import post_project_data


def process_payout(url, data):
    if getattr(settings, 'CELERY_RESULT_BACKEND', None):
        post_project_data.delay(url, data)
    else:
        post_project_data(url, data)
