from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect


class ApproveActivities(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        for activity in self.instance.activities.filter(status='submitted'):
            activity.states.approve(save=True)

    def __unicode__(self):
        return _('Approve related activities')


class RejectActivities(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        for activity in self.instance.activities.all():
            activity.states.reject(save=True)

    def __unicode__(self):
        return _('Reject related activities')
