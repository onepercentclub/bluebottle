from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import DeadlineParticipant


class CreateDeadlineParticipantEffect(Effect):
    title = _('Create participant for this registration')
    template = 'admin/create_deadline_participant.html'

    def post_save(self, **kwargs):
        DeadlineParticipant.objects.get_or_create(
            registration=self.instance,
            activity=self.instance.activity,
            user=self.instance.user,
        )
