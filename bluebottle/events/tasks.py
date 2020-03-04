from datetime import timedelta
from celery.schedules import crontab
from celery.task import periodic_task
from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
import logging

from bluebottle.events.models import Event
from bluebottle.events.messages import EventReminder

logger = logging.getLogger('bluebottle')


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_event_start",
    ignore_result=True
)
def check_event_start():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Start events that are running now
            events = Event.objects.filter(
                start__lte=now(),
                status__in=['full', 'open']
            ).all()

            for event in events:
                if len(event.participants):
                    event.transitions.start()
                else:
                    event.transitions.close()

                event.save()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_event_end",
    ignore_result=True
)
def check_event_end():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Close events that are over
            events = Event.objects.filter(
                end__lte=now(),
                status__in=['running']
            ).all()

            for event in events:
                event.transitions.succeed()
                event.save()


@periodic_task(
    run_every=(crontab(minute='*/15')),
    name="check_event_reminder",
    ignore_result=True
)
def check_event_reminder():
    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            # Close events that are over
            events = Event.objects.filter(
                end__lte=now() + timedelta(days=5),
                status__in=['open', 'full'],
            ).all()

            for event in events:
                EventReminder(event).compose_and_send(once=True)
