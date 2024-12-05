from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from bluebottle.activities.models import (
    EffortContribution,
    Contribution,
    Organizer
)
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.collect.models import CollectContributor
from bluebottle.funding.models import MoneyContribution
from bluebottle.time_based.models import (
    DateParticipant,
    DeadlineParticipant,
    TeamScheduleParticipant,
    ScheduleParticipant,
    TimeContribution,
    PeriodicParticipant,
)


def is_almost_equal(first, second):
    return not first or abs((first - second).total_seconds()) < 1


def fix_contribution(contribution, date, fix):
    if fix:
        contribution.start = date
        contribution.save()
    else:
        pass

def run(*args):
    fix = 'fix' in args

    for client in Client.objects.all():
        with LocalTenant(client):
            total = 0
            for contribution in Contribution.objects.all():
                contributor = contribution.contributor

                if not contributor:
                    continue

                if isinstance(contribution, EffortContribution):
                    if isinstance(contributor, Organizer):
                        continue
                    else:
                        if not is_almost_equal(contribution.start, contributor.created):
                            fix_contribution(contribution, contributor.created, fix)
                            total += 1

                if isinstance(contribution, TimeContribution):
                    if isinstance(contributor, DateParticipant):
                        if contribution.slot_participant:
                            slot = contribution.slot_participant.slot

                            if not is_almost_equal(contribution.start, slot.start):
                                fix_contribution(contribution, slot.start, fix)
                                total += 1
                        else:
                            continue

                    elif isinstance(contributor, DeadlineParticipant):
                        if not is_almost_equal(contribution.start, contributor.created):
                            fix_contribution(contribution, contributor.created, fix)
                            total += 1

                    elif isinstance(contributor, PeriodicParticipant):
                        if not is_almost_equal(contribution.start, contributor.slot.start):
                            fix_contribution(contribution, contributor.slot.start, fix)
                            total += 1

                    elif isinstance(contributor, (TeamScheduleParticipant, ScheduleParticipant)):
                        if contributor.slot.start:
                            if not is_almost_equal(contribution.start, contributor.slot.start):
                                fix_contribution(contribution, contributor.slot.start, fix)
                                total += 1
                        else:
                            if not is_almost_equal(contribution.start, contributor.created):
                                fix_contribution(contribution, contributor.slot.start, fix)
                                total += 1

                    else:
                        print('!!!!!!!!!!!!!!! missing type')
                        __import__('ipdb').set_trace()

                if isinstance(contribution, MoneyContribution):
                    if not is_almost_equal(contribution.start, contributor.created):
                        fix_contribution(contribution, contributor.created, fix)
                        total += 1

                if isinstance(contribution, CollectContributor):
                    if not is_almost_equal(contribution.start, contributor.created):
                        fix_contribution(contribution, contributor.created, fix)
                        total += 1

            print(
                f'Checking {client.client_name} {total} {Contribution.objects.count()}'
            )
    if not fix:
        print("☝️ Add '--script-args=fix' to the command to actually fix the activities.")
