from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import ScheduleActivity, TeamScheduleRegistration, TeamMember


class CreateTeamRegistrationEffect(Effect):
    title = _('Create registration for this team')
    template = 'admin/create_team_registration.html'

    def without_registration(self):
        return not self.instance.registration

    def get_registration_model(self):
        if isinstance(self.instance.activity, ScheduleActivity):
            return TeamScheduleRegistration
        raise ValueError(f'No registration defined for activity model {self.instance.activity.__class__.__name__}')

    def post_save(self, **kwargs):
        registration = self.get_registration_model().objects.create(
            activity=self.instance.activity,
            user=self.instance.user,
            status='accepted'
        )
        self.instance.registration = registration
        self.instance.save()

    conditions = [
        without_registration
    ]


class CreateCaptainTeamMemberEffect(Effect):
    title = _('Create team member for the team captain')
    template = 'admin/create_captain_team_member.html'

    def without_team_members(self):
        return not self.instance.team_members.exists()

    def post_save(self, **kwargs):
        TeamMember.objects.create(
            team=self.instance,
            user=self.instance.user,
        )

    conditions = [
        without_team_members
    ]
