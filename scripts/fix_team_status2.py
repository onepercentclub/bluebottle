from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import Team, TeamMember, TeamScheduleParticipant


def run(*args):
    fix = 'fix' in args
    for client in Client.objects.all():
        with (LocalTenant(client)):
            new_teams = Team.objects.filter(status='new', registration__status='accepted')
            if new_teams.count():
                print(f"{client.client_name}:  {new_teams.count()} inconsistent teams.")
                print(f"Team ID: {new_teams.first().id}")
                if fix:
                    new_teams.update(status='accepted')
                    print(f"Fixed {new_teams.count()} teams.")

            team_members = TeamMember.objects.filter(status__in=['accepted', 'new'])
            if team_members.count():
                print(f"{client.client_name}:  {team_members.count()} inconsistent team members.")
                if fix:
                    team_members.update(status='active')
                    print(f"Fixed {new_teams.count()} team members.")

            participants = TeamScheduleParticipant.objects.filter(status='succeeded', slot__status='new')
            if participants.count():
                print(f"{client.client_name}: {participants.count()} inconsistent team slot participants.")
                if fix:
                    participants.update(status='accepted')
                    for participant in participants:
                        participant.contributions.update(status='new')
                    print(f"Fixed {new_teams.count()} team team slot participants.")

    if not fix:
        print("☝️ Add '--script-args=fix' to the command to actually fix the statuses.")
