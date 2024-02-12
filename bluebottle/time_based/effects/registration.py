from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect


class CreateDeadlineParticipantEffect(Effect):
    title = _('Create participant for this registration')
    template = 'admin/create_deadline_participant.html'

    def post_save(self, **kwargs):
        self.instance.participants.create(
            activity=self.instance.activity,
            user=self.instance.user,
            registration=self.instance,
        )

    def is_valid(self):
        return not self.instance.participants.exists()
