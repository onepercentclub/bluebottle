from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import ScheduleActivity, TeamScheduleRegistration, TeamMember, TeamScheduleSlot


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


class CreateTeamSlotEffect(Effect):
    title = _('Create slot for this team')
    template = 'admin/create_team_slot.html'

    def without_slot(self):
        return not self.instance.slots.exists()

    def get_slot_model(self):
        if isinstance(self.instance.activity, ScheduleActivity):
            return TeamScheduleSlot
        raise ValueError(f'No slot defined for activity model {self.instance.activity.__class__.__name__}')

    def post_save(self, **kwargs):
        activity = self.instance.activity
        self.get_slot_model().objects.create(
            activity=activity,
            is_online=activity.is_online,
            location_id=activity.location_id,
            location_hint=activity.location_hint,
            duration=activity.duration,
            online_meeting_url=activity.online_meeting_url,
            team=self.instance
        )

    conditions = [
        without_slot
    ]


class CreateTeamMemberSlotParticipantsEffect(Effect):
    title = _('Create participants for this team member')
    template = 'admin/create_team_member_slot_participants.html'

    def post_save(self, **kwargs):
        team_member = self.instance
        for slot in self.instance.team.slots.filter(status__in=['new', 'running', 'scheduled', 'finished']).all():
            slot.participants.get_or_create(
                user=team_member.user,
                team_member=team_member,
                activity=slot.activity,
                registration=self.instance.team.registration,
            )


class DeleteTeamMemberSlotParticipantsEffect(Effect):
    title = _('Delete participants for this team member')
    template = 'admin/delete_team_member_slot_participants.html'

    def post_save(self, **kwargs):
        team_member = self.instance
        team_member.participants.all().delete()
