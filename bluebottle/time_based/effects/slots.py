from django.utils.timezone import now
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect


class CreateTeamSlotParticipantsEffect(Effect):
    title = _('Create participants for this team slot')
    template = 'admin/create_team_slot_participants.html'

    def post_save(self, **kwargs):
        for team_member in self.instance.team.team_members.filter(status__in=['new', 'accepted']).all():
            slot = self.instance
            slot.participants.get_or_create(
                user=team_member.user,
                activity=slot.activity,
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
