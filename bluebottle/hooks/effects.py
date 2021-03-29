from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import Effect

from bluebottle.hooks.signals import hook


class BaseSignalEffect(Effect):
    title = _('Activate hook')
    template = 'admin/hook_effect.html'

    def post_save(self, **kwargs):
        hook.send(sender=self.instance.__class__, event=self.event, instance=self.instance)

    def __repr__(self):
        return '<Effect: Activate hook>'

    def __str__(self):
        return _('Activate hook for {}').format(self.instance)

    @property
    def is_valid(self):
        return all([condition(self) for condition in self.conditions])


def SignalEffect(_event):
    class SignalEffect(BaseSignalEffect):
        event = _event

    return SignalEffect
