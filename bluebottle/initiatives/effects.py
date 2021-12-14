from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import Effect


class RemoveLocationEffect(Effect):
    "Remove location from initiative"

    title = _('Clear the location of the initiative when the application is global')
    template = 'admin/remove_location.html'

    def pre_save(self, **kwargs):
        if self.instance.is_global:
            self.instance.location = None

    @property
    def is_valid(self):
        return super().is_valid and self.instance.is_global and self.instance.location

    def __str__(self):
        return str(_('Remove location'))
