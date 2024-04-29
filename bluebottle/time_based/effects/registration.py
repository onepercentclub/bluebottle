from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import PeriodicSlot


class CreateParticipantEffect(Effect):
    title = _('Create participant for this registration')
    template = 'admin/create_participant.html'

    def post_save(self, **kwargs):
        self.instance.participants.create(
            activity=self.instance.activity,
            user=self.instance.user,
            registration=self.instance,
        )

    def is_valid(self):
        return not self.instance.participants.exists()


class CreateTeamMemberParticipantEffect(Effect):
    title = _('Create participant for this team member')
    template = 'admin/create_participant.html'

    def post_save(self, **kwargs):
        team_captain = self.instance.team.participants.first()
        self.instance.participants.create(
            activity=self.instance.activity,
            user=self.instance.user,
            slot=team_captain.slot,
            registration=self.instance,
        )

    def is_valid(self):
        return not self.instance.participants.exists()


class CreateInitialPeriodicParticipantEffect(Effect):
    title = _("Create initial periodic participant for this registration")
    template = "admin/create_participant.html"

    def post_save(self, **kwargs):
        try:
            slot = self.instance.activity.slots.get(status__in=["new", "running"])
            self.instance.participants.create(
                activity=self.instance.activity,
                user=self.instance.user,
                registration=self.instance,
                slot=slot,
            )
        except PeriodicSlot.DoesNotExist:
            pass

    def is_valid(self):
        return not self.instance.participants.exists()
