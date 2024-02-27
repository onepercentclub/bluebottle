from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect


class CreateParticipantEffect(Effect):
    title = _('Create participant for this registration')
    template = 'admin/create_participant.html'

    def post_save(self, **kwargs):
        if self.instance.activity.slots.exists():
            slot = self.instance.activity.slots.last()
        else:
            slot = None

        self.instance.participants.create(
            activity=self.instance.activity,
            user=self.instance.user,
            registration=self.instance,
            slot=slot
        )

    def is_valid(self):
        return not self.instance.participants.exists()
