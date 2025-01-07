from bluebottle.activities.models import Contributor
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import TimeContribution


def run(*args):
    fix = 'fix' in args
    total_errors = False
    for client in Client.objects.all():
        with (LocalTenant(client)):

            for contribution in TimeContribution.objects.filter(contribution_type="preparation"):

                try:
                    contributor = contribution.contributor
                    if contributor:
                        related_contribution_statuses = [
                            related_contribution.status for related_contribution
                            in contributor.contributions.exclude(pk=contribution.pk)
                        ]

                        if (
                            contribution.status == 'succeeded' and
                            'succeeded' not in related_contribution_statuses and
                            contributor.status != 'accepted'
                        ):
                            print('succeeded incorrectly')
                            print(contribution.status, related_contribution_statuses)
                            __import__('ipdb').set_trace()

                        if (
                            contribution.status == 'failed' and
                            not all([status == 'failed' for status in related_contribution_statuses])
                        ):
                            print('failed incorrectly')
                            print(contribution.status, related_contribution_statuses)

                            if contributor.status == 'accepted':
                                contribution.status = 'succeeded'
                                contribution.save()
                                print('should be succeeded')
                            else:
                                __import__('ipdb').set_trace()
                    else:
                        print(f'no contributor for {contribution.pk}')
                except Contributor.DoesNotExist:
                    print(f'no contributor for {contribution.pk}')

    if not fix and total_errors:
        print("☝️ Add '--script-args=fix' to the command to actually fix the activities.")

    if not total_errors:
        print("No errors found! 🎉🎉🎉")
