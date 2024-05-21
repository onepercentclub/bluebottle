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
