from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect


class SetTimeSpent(Effect):
    post_save = True
    save = True

    def execute(self, **kwargs):
        if not self.instance.time_spent:
            self.instance.time_spent = self.instance.activity.duration + (self.instance.activity.preparation or 0)

    def __unicode__(self):
        return _('Set time spent to {} on {}').format(
            self.instance.activity.duration,
            self.instance
        )


class ClearTimeSpent(Effect):
    post_save = True

    def execute(self, **kwargs):
        self.instance.time_spent = 0

    def __unicode__(self):
        return _('Set time spent to 0 on {}').format(
            self.instance
        )
