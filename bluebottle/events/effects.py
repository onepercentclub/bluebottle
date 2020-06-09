from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import Effect


class SetTimeSpent(Effect):
    "Set time spent on participants"
    post_save = False

    def execute(self, **kwargs):
        if not self.instance.time_spent:
            self.instance.time_spent = self.instance.activity.duration

    def __unicode__(self):
        return unicode(_('Set time spent to {} on {}').format(
            self.instance.activity.duration,
            self.instance
        ))


class ResetTimeSpent(Effect):
    "Set time spent to 0 if it was not overriden"
    post_save = False

    def execute(self, **kwargs):
        if self.instance.time_spent == self.instance.activity.duration:
            self.instance.time_spent = 0

    def __unicode__(self):
        return unicode(_('Reset time spent to 0 on {}').format(
            self.instance
        ))
