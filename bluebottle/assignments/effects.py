from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect


class SetTimeSpent(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        self.instance.time_spent = self.instance.activity.time_needed

    def __unicode__(self):
        return _('Set time spent')


class ClearTimeSpent(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        self.instance.time_spent = 0

    def __unicode__(self):
        return _('Clear time spent')
