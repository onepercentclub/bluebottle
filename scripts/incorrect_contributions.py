
from django.db.models import Count, Q

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import TimeContribution


def run(*args):
    for client in Client.objects.all():
        with (LocalTenant(client)):
            failed_contributions = TimeContribution.objects.filter(
                status='succeeded',
                slot_participant_id__isnull=False
            ).exclude(
                Q(slot_participant__status__in=('registered', )) &
                Q(contributor__status__in=('accepted', 'new', )) &
                Q(contributor__activity__status__in=('open', 'succeeded', 'full'))

            )
            succeeded_contributions = TimeContribution.objects.filter(
                status='failed',
                slot_participant_id__isnull=False,
                contributor__status__in=('accepted', 'new',),
                slot_participant__status__in=('registered',),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )

            if failed_contributions.count() or succeeded_contributions.count():
                print(f'{client.name}:\nfailed but should be succeeded: {succeeded_contributions.count()}\nsucceeded but should be failed: {failed_contributions.count()}\n\n')


