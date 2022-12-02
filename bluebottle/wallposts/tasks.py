import logging

from celery.schedules import crontab
from celery.task import periodic_task
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.wallposts.models import Wallpost

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute=0, hour=10)),
    name="data_retention_wallposts",
    ignore_result=True
)
def data_retention_wallposts_task():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            settings = MemberPlatformSettings.objects.get()
            if settings.retention_anonymize:
                history = now() - relativedelta(months=settings.retention_anonymize)
                Wallpost.objects.filter(created__lt=history, author__isnull=False).update(
                    ip_address=None,
                    author=None,
                    editor=None
                )
            if settings.retention_delete:
                history = now() - relativedelta(months=settings.retention_delete)
                Wallpost.objects.filter(created__lt=history).all().delete()
