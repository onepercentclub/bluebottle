from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect


class ApproveActivities(Effect):
    post_save = True
    conditions = []

    title = _('Change status of related objects')

    def execute(self, **kwargs):
        for activity in self.instance.activities.filter(status='submitted'):
            activity.states.approve(save=True)

    def __unicode__(self):
        return _('Approve related activities')


class RejectActivities(Effect):
    post_save = True
    conditions = []

    title = _('Change status of related objects')

    @property
    def description(self):
        return unicode(self)

    def execute(self, **kwargs):
        for activity in self.instance.activities.all():
            activity.states.reject(save=True)

    def __unicode__(self):
        return _('Reject related activities')


class CancelActivities(Effect):
    post_save = True
    conditions = []

    title = _('Change status of related objects')

    @property
    def description(self):
        return unicode(self)

    def execute(self, **kwargs):
        for activity in self.instance.activities.all():
            activity.states.cancel(save=True)

    def __unicode__(self):
        return _('Cancel related activities')


class DeleteActivities(Effect):
    post_save = True
    conditions = []

    title = _('Change status of related objects')

    @property
    def description(self):
        return unicode(self)

    def execute(self, **kwargs):
        for activity in self.instance.activities.all():
            activity.states.delete(save=True)

    def __unicode__(self):
        return _('Delete related activities')
