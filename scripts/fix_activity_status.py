from django.db.models import Q
from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import DateActivity


def run(*args):
    fix = 'fix' in args
    for client in Client.objects.all():
        with LocalTenant(client):
            full_activities = DateActivity.objects.filter(
                slots__status='open',
                status__in=['full', 'succeeded'],
            ).filter(
                Q(registration_deadline__gt=now()) | Q(registration_deadline__isnull=True)
            ).all()

            open_activities = DateActivity.objects.exclude(
                slots__status='open'
            ).filter(
                status='open'
            ).all()

            if full_activities.count() > 0 or open_activities.count() > 0:
                print("### Tenant {}".format(client.name))
            for activity in full_activities:
                print(
                    "Activity {title} is {status} but there are still open slots.".format(
                        title=activity.title,
                        status=activity.status
                    )
                )
                if fix:
                    activity.states.reopen(save=True)
            for activity in open_activities:
                print(
                    "Activity {title} is {status} but there aren't any open slots.".format(
                        title=activity.title,
                        status=activity.status
                    )
                )
                if fix:
                    activity.states.lock(save=True)
    if not fix:
        print("☝️ Add '--script-args=fix' to the command to actually fix the activities.")
