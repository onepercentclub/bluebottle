from django.db.models import Count

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.models import Team, TeamScheduleRegistration

REGISTRATION_TEAM_TRANSITIONS = {
    'accepted': 'accept',
    'rejected': 'reject',
    'withdrawn': 'withdraw',
}


def get_clients(args):
    tenant = next((arg.split('=', 1)[1] for arg in args if arg.startswith('tenant=')), None)
    if tenant:
        return Client.objects.filter(schema_name=tenant)
    return Client.objects.all()


def get_registrations_without_team():
    return TeamScheduleRegistration.objects.filter(
        activity__team_activity='teams',
    ).annotate(
        team_count=Count('teams')
    ).filter(
        team_count=0,
    )


def fix_registration(registration, fix):
    team, _c = Team.objects.get_or_create(
        activity=registration.activity,
        user=registration.user,
        registration__isnull=True,
    )
    if not team.name:
        team.name = f'Team {registration.user.full_name}'

    if fix:
        team.registration = registration
        if registration.status == 'new':
            team.status = 'new'
        elif registration.status == 'accepted':
            team.status = 'accepted'
        else:
            team.status = registration.status
        team.save(run_triggers=False)

    return True


def run(*args):
    fix = 'fix' in args
    total_issues = 0

    for client in get_clients(args):
        with LocalTenant(client):
            registrations = list(get_registrations_without_team())
            if not registrations:
                continue

            total_issues += len(registrations)
            print(f"{client.client_name}: {len(registrations)} team registrations without team.")
            for registration in registrations:
                print(
                    f"  Registration {registration.id} "
                    f"(activity={registration.activity_id}, "
                    f"user={registration.user_id}, status={registration.status}, "
                )

            if fix:
                fixed = sum(
                    1 for registration in registrations
                    if fix_registration(registration, fix)
                )
                if fixed:
                    print(f"  Linked {fixed} registrations to existing teams.")

    if total_issues:
        if not fix:
            print("☝️ Add '--script-args=fix' to the command to link registrations to existing teams.")
    else:
        print("No team registrations without team found.")
