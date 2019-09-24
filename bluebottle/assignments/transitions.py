from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem

from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions
from bluebottle.assignments.messages import AssignmentApplicationMessage
from bluebottle.assignments.messages import AssignmentCompletedMessage, AssignmentExpiredMessage, \
    AssignmentClosedMessage
from bluebottle.follow.models import unfollow, follow
from bluebottle.fsm import transition


class AssignmentTransitions(ActivityTransitions):
    class values(ActivityTransitions.values):
        running = ChoiceItem('running', _('running'))

    @transition(
        field='status',
        source=values.open,
        target=values.running,
    )
    def start(self, **kwargs):
        pass

    @transition(
        field='status',
        source=values.running,
        target=values.succeeded,
        permissions=[ActivityTransitions.is_system],
        messages=[AssignmentCompletedMessage]
    )
    def succeed(self, **kwargs):
        for member in self.instance.accepted_applicants:
            member.succeed()
            member.save()

    @transition(
        field='status',
        source=values.running,
        target=values.closed,
        permissions=[ActivityTransitions.is_system],
        messages=[AssignmentClosedMessage]
    )
    def close(self, **kwargs):
        for member in self.instance.accepted_applicants:
            member.fail()
            member.save()

    @transition(
        field='status',
        source=[values.open, values.running],
        target=values.closed,
        permissions=[ActivityTransitions.is_system],
        messages=[AssignmentExpiredMessage]
    )
    def expire(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[
            values.closed,
            values.succeeded,
            values.running
        ],
        target=values.open,
    )
    def extend_end_date(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[
            values.closed,
            values.succeeded
        ],
        target=values.running,
    )
    def extend(self, **kwargs):
        pass


class ApplicantTransitions(ContributionTransitions):
    class values(ContributionTransitions.values):
        draft = ChoiceItem('draft', _('draft'))
        accepted = ChoiceItem('accepted', _('accepted'))
        rejected = ChoiceItem('rejected', _('rejected'))
        withdrawn = ChoiceItem('withdrawn', _('withdrawn'))
        active = ChoiceItem('attending', _('attending'))

    default = values.draft

    def assignment_is_open(self):
        if self.instance.activity.status != ActivityTransitions.values.open:
            return _('The event is not open')

    @transition(
        source=values.draft,
        target=ContributionTransitions.values.new,
        permissions=[ContributionTransitions.is_system],
        messages=[AssignmentApplicationMessage]
    )
    def submit(self):
        pass

    @transition(
        field='status',
        source=[values.new, values.rejected],
        target=values.accepted,
        conditions=[assignment_is_open],
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def accept(self):
        pass

    @transition(
        field='status',
        source=[values.new, values.accepted],
        target=values.rejected,
        conditions=[assignment_is_open],
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def reject(self):
        unfollow(self.instance.user, self.instance.activity)

    @transition(
        field='status',
        source=[values.new, values.accepted],
        target=values.withdrawn,
        conditions=[assignment_is_open],
        permissions=[ContributionTransitions.is_user]
    )
    def withdraw(self):
        unfollow(self.instance.user, self.instance.activity)

    @transition(
        source=values.withdrawn,
        target=values.new,
        conditions=[assignment_is_open],
        permissions=[ContributionTransitions.is_user]
    )
    def reapply(self):
        follow(self.instance.user, self.instance.activity)

    @transition(
        field='status',
        source=values.accepted,
        target=values.active,
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def activate(self):
        pass

    @transition(
        field='status',
        source=[values.active, values.failed],
        target=values.succeeded,
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def succeed(self):
        pass

    @transition(
        field='status',
        source=[values.succeeded, values.active],
        target=values.failed,
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def fail(self):
        unfollow(self.instance.user, self.instance.activity)
        self.time_spent = None
