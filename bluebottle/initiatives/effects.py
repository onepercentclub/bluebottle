from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.fsm.state import TransitionNotPossible


class TransitionActivitiesEffect(Effect):
    title = _('Change activity status')
    transition = ''

    @property
    def activities(self):
        return self.instance.activities

    def execute(self, **kwargs):
        failed = []
        for activity in self.activities.all():

            try:
                getattr(activity.states, self.transition)(save=True)
            except TransitionNotPossible:
                failed.append(activity)
        if len(failed):
            raise TransitionNotPossible(
                _("Effect failed. Could not transition {count} activities.").format(count=len(failed))
            )

    @property
    def description(self):
        if self.activities.count() < 3:
            return "{} {}".format(
                self.transition,
                " + ".join('"{}"'.format(a.title) for a in self.activities.all()))
        return _('{transition} "{activity}" and {count} other activities.').format(
            transition=self.transition.title(),
            activity=self.activities.first(),
            count=self.activities.count() - 1
        )

    def __unicode__(self):
        return _('{transition} related activities').format(transition=self.transition.title())


class ApproveActivitiesEffect(TransitionActivitiesEffect):
    post_save = True
    conditions = []
    transition = 'approve'

    @property
    def activities(self):
        return self.instance.activities.filter(status='submitted')


class SubmitActivitiesEffect(TransitionActivitiesEffect):
    post_save = True
    conditions = []
    transition = 'submit'

    @property
    def activities(self):
        return self.instance.activities.filter(status__in=['draft', 'needs_work'])


class RejectActivitiesEffect(TransitionActivitiesEffect):
    post_save = True
    conditions = []
    transition = 'reject'


class CancelActivitiesEffect(TransitionActivitiesEffect):
    post_save = True
    conditions = []
    transition = 'cancel'


class DeleteActivitiesEffect(TransitionActivitiesEffect):
    post_save = True
    conditions = []
    transition = 'delete'


class RestoreActivitiesEffect(TransitionActivitiesEffect):
    post_save = True
    conditions = []
    transition = 'restore'

    @property
    def activities(self):
        return self.instance.activities.filter(
            status__in=['cancelled', 'rejected', 'deleted']
        )
