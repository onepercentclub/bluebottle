from django.utils.timezone import now
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect


class CreateTeamSlotParticipantsEffect(Effect):
    title = _('Create participants for this team slot')
    template = 'admin/create_team_slot_participants.html'

    def post_save(self, **kwargs):
        if not self.instance.team_id:
            return
        for team_member in self.instance.team.team_members.filter(status='active').all():
            slot = self.instance
            slot.participants.get_or_create(
                user=team_member.user,
                remote_user=team_member.remote_user,
                team_member=team_member,
                activity=slot.activity,
                registration=self.instance.team.registration,
            )


class SetContributionsStartEffect(Effect):
    title = _('Set contributions start date')
    template = 'admin/time_based/set_contributions_start.html'

    def is_valid(self):
        return not self.instance.start

    def post_save(self, **kwargs):
        if not self.instance.start:
            for participant in self.instance.participants.all():
                participant.contributions.update(start=now())


class LockActivityEffect(Effect):
    title = _('Lock activity')
    display = False

    def is_valid(self):
        return True

    def post_save(self, **kwargs):
        if (
            all(slot.status == 'full' for slot in self.instance.activity.slots.all()) and
            self.instance.activity.status != 'full'
        ):
            self.instance.activity.states.lock(save=True)
