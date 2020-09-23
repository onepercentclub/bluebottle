from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect


class SetTimeSpent(Effect):
    template = 'admin/set_time_spent_effect.html'

    def post_save(self, **kwargs):
        if not self.instance.time_spent:
            self.instance.time_spent = self.time_spent

    @property
    def time_spent(self):
        return self.instance.activity.duration + (self.instance.activity.preparation or 0)

    def __unicode__(self):
        return _('Set time spent to {} on {}').format(
            self.instance.activity.duration,
            self.instance
        )


class ClearTimeSpent(Effect):
    template = 'admin/reset_time_spent_effect.html'

    def post_save(self, **kwargs):
        self.instance.time_spent = 0

    def __unicode__(self):
        return _('Set time spent to 0 on {}').format(
            self.instance
        )
