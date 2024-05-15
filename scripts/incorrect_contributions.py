
from django.db.models import Q

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import TimeContribution


def run(*args):
    fix = 'fix' in args
    total_errors = False
    for client in Client.objects.all():
        with (LocalTenant(client)):
            succeeded_contributions = TimeContribution.objects.filter(
                status='succeeded',
                slot_participant_id__isnull=False
            ).exclude(
                Q(slot_participant__status__in=('registered', )) &
                Q(contributor__status__in=('accepted', 'new', )) &
                Q(contributor__activity__status__in=('open', 'succeeded', 'full'))
            )
            failed_contributions = TimeContribution.objects.filter(
                status='failed',
                slot_participant_id__isnull=False,
                contributor__status__in=('accepted', 'new',),
                slot_participant__status__in=('registered',),
                contributor__activity__status__in=('open', 'succeeded', 'full',)
            )

            errors = failed_contributions.count() or succeeded_contributions.count()
            if errors:
                total_errors = True
                print("### Tenant {}:".format(client.name))
                print(f'failed but should be succeeded: {failed_contributions.count()}')
                print(f'succeeded but should be failed: {succeeded_contributions.count()}')
                print('\n')
                if fix:
                    succeeded_contributions.update(status='failed')
                    failed_contributions.update(status='succeeded')

    if not fix and total_errors:
        print("☝️ Add '--script-args=fix' to the command to actually fix the activities.")

    if not total_errors:
        print("No errors found! 🎉🎉🎉")
