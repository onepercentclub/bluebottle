from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect, TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger


class ApproveActivity(Effect):
    post_save = True
    conditions = []

    def execute(self):
        for activity in self.instance.activities.filter(review_status='submitted'):
            activity.review_states.approve()
            activity.save()

    def __unicode__(self):
        return _('Approve related activities')


class Complete(ModelChangedTrigger):
    effects = [TransitionEffect('submit')]

    @property
    def is_valid(self):
        "There are no errors or missing fields"
        return (
            not list(self.instance.errors) and
            not list(self.instance.required)
        )
