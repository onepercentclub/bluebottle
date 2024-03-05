from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect


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


class CreateInitialPeriodicParticipantEffect(Effect):
    title = _("Create initial periodic participant for this registration")
    template = "admin/create_participant.html"

    def post_save(self, **kwargs):
        slot = self.instance.activity.slots.get(status__in=["new", "running"])
        self.instance.participants.create(
            activity=self.instance.activity,
            user=self.instance.user,
            registration=self.instance,
            slot=slot
        )

    def is_valid(self):
        return not self.instance.participants.exists()
