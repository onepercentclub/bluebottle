from celery.schedules import crontab
from celery.task import periodic_task
from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
import logging

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_event_start",
    ignore_result=True
)
def check_event_start():
    from bluebottle.events.models import Event
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Start events that are running now
            events = Event.objects.filter(
                datetime_start__lte=now(),
                datetime_end__gte=now(),
                status__in=['full', 'open']
            ).all()

            for event in events:
                event.start()
                event.save()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_event_end",
    ignore_result=True
)
def check_event_end():
    from bluebottle.events.models import Event
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Close events that are over
            events = Event.objects.filter(
                datetime_end__lte=now(),
                status__in=['running']
            ).all()

            for event in events:
                event.done()
                event.save()
