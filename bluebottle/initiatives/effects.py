from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect, TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger


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


class Complete(ModelChangedTrigger):
    effects = [TransitionEffect('submit')]

    @property
    def is_valid(self):
        "There are no errors or missing fields"
        return (
            not list(self.instance.errors) and
            not list(self.instance.required)
        )
