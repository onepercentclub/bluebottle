from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import Effect


class SetTimeSpent(Effect):
    "Set time spent on participants"
    post_save = False
    title = _('Reset time spent')

    def execute(self, **kwargs):
        if not self.instance.time_spent:
            self.instance.time_spent = self.instance.activity.duration

    def __unicode__(self):
        return unicode(_('Set time spent to {duration} on {participant}').format(
            duration=self.instance.activity.duration or _('event duration'),
            participant=self.instance
        ))


class ResetTimeSpent(Effect):
    "Set time spent to 0 if it was not overriden"
    post_save = False
    title = _('Reset time spent')

    def execute(self, **kwargs):
        if self.instance.time_spent == self.instance.activity.duration:
            self.instance.time_spent = 0

    def __unicode__(self):
        return _('Set time spent to 0 on {}').format(
            self.instance
        )
