from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import Effect


class SetTimeSpent(Effect):
    """Set time spent on participants"""
    post_save = False
    title = _('Reset time spent')

    template = 'admin/set_time_spent_effect.html'

    def execute(self, **kwargs):
        if not self.instance.time_spent:
            self.instance.time_spent = self.instance.activity.duration

    @property
    def time_spent(self):
        return self.instance.activity.duration

    def __unicode__(self):
        participant = self.instance
        if not self.instance.id:
            participant = _('participant')
        return str(_('Set time spent to {duration} on {participant}').format(
            duration=self.instance.activity.duration or _('event duration'),
            participant=participant
        ))


class ResetTimeSpent(Effect):
    """Set time spent to 0 if it was not overridden"""
    post_save = False
    title = _('Reset time spent')

    template = 'admin/reset_time_spent_effect.html'

    def execute(self, **kwargs):
        if self.instance.time_spent == self.instance.activity.duration:
            self.instance.time_spent = 0

    @property
    def is_valid(self):
        return self.instance.time_spent != 0

    def __unicode__(self):
        participant = self.instance
        if not self.instance.id:
            participant = _('participant')
        return _('Set time spent to 0 on {participant}').format(
            participant=participant
        )
