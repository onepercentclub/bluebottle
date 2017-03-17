import requests
from requests.exceptions import MissingSchema, RequestException

from celery import shared_task

from django.core.exceptions import ImproperlyConfigured


@shared_task(bind=True, default_retry_delay=5 * 60, max_retries=5)
def post_project_data(self, url, data):
    try:
        response = requests.post(url, data)
        if response.content != '{"status": "success"}':
            raise SystemError("Could not trigger payout")

        from bluebottle.projects.models import Project
        project = Project.objects.get(pk=data['project_id'])
        project.payout_status = 'created'
        project.save()
    except MissingSchema:
        raise ImproperlyConfigured("Incorrect Payout URL")
    except RequestException as exc:
        raise self.retry(exc=exc)
    except SystemError as exc:
        raise self.retry(exc=exc)
