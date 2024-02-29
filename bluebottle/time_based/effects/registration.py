from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import DeadlineActivity


class CreateParticipantEffect(Effect):
    title = _('Create participant for this registration')
    template = 'admin/create_participant.html'

    def post_save(self, **kwargs):
        if not isinstance(self.instance.activity, DeadlineActivity) and self.instance.activity.slots.exists():
            slot = self.instance.activity.slots.last()
            self.instance.participants.create(
                activity=self.instance.activity,
                user=self.instance.user,
                registration=self.instance,
                slot=slot
            )
        else:
            self.instance.participants.create(
                activity=self.instance.activity,
                user=self.instance.user,
                registration=self.instance,
            )

    def is_valid(self):
        return not self.instance.participants.exists()
