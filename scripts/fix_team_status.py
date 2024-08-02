from datetime import timedelta

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import Team


def run(*args):
    fix = 'fix' in args
    for client in Client.objects.all():
        with (LocalTenant(client)):
            for team in Team.objects.all():
                slot = team.slots.get()
                if slot.start:

                    delta = slot.start - slot.created

                    if delta < timedelta(minutes=1) and delta > timedelta(minutes=-1):
                        if team.status == 'succeeded':
                            team.status = 'new'

                            if fix:
                                team.save(run_triggers=False)

                        slot.start = None
                        slot.status = team.status
                        if fix:
                            slot.save(run_triggers=False)

                        for member in team.team_members.all():
                            member.status = team.status
                            if fix:
                                member.save(run_triggers=False)

                            participant = member.participants.get()
                            contribution = member.participants.get().contributions.get()

                            if team.status == 'new' and participant.status in ('succeeded', 'new'):
                                participant.status = 'new'
                                if fix:
                                    contribution.save(run_triggers=False)

                                if team.activity.status != 'succeeded' and contribution.status == 'succeeded':
                                    contribution.status = 'new'
                                    if fix:
                                        contribution.save(run_triggers=False)

                            print(
                                delta,
                                team.activity.status,
                                team.status,
                                slot.status,
                                member.status,
                                participant.status,
                                contribution.status
                            )

    if not fix:
        print("☝️ Add '--script-args=fix' to the command to actually fix the statuses.")
