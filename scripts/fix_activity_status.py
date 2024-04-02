from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import DateActivity


def run(*args):
    for client in Client.objects.all():
        with LocalTenant(client):
            full_activities = DateActivity.objects.filter(
                slots__status='open'
            ).filter(
                status__in=['full', 'succeeded']
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
                # activity.states.reopen(save=True)
            for activity in open_activities:
                print(
                    "Activity {title} is {status} but there aren't any open slots.".format(
                        title=activity.title,
                        status=activity.status
                    )
                )
                # activity.states.lock(save=True)
