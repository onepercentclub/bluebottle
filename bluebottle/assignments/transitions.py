from django.utils.translation import ugettext_lazy as _
from djchoices.choices import ChoiceItem

from bluebottle.activities.transitions import ActivityTransitions, ContributionTransitions
from bluebottle.assignments.messages import ApplicantRejectedMessage, ApplicantAcceptedMessage
from bluebottle.assignments.messages import AssignmentApplicationMessage
from bluebottle.assignments.messages import AssignmentCompletedMessage, AssignmentExpiredMessage, \
    AssignmentClosedMessage
from bluebottle.follow.models import unfollow, follow
from bluebottle.fsm import transition


class AssignmentTransitions(ActivityTransitions):
    class values(ActivityTransitions.values):
        running = ChoiceItem('running', _('running'))
        full = ChoiceItem('full', _('full'))

    @transition(
        field='status',
        source=[values.open, values.full],
        target=values.running,
    )
    def start(self, **kwargs):
        for member in self.instance.accepted_applicants:
            member.transitions.activate()
            member.save()

    @transition(
        field='status',
        source=values.open,
        target=values.full,
    )
    def lock(self, **kwargs):
        pass

    @transition(
        field='status',
        source=[
            values.full,
            values.closed,
            values.deleted,
            values.open
        ],
        target=values.open,
    )
    def reopen(self, **kwargs):
        self.instance.review_transitions.organizer_succeed()

    @transition(
        field='status',
        source=[values.running, values.open, values.full],
        target=values.succeeded,
        permissions=[ActivityTransitions.is_system],
        messages=[AssignmentCompletedMessage]
    )
    def succeed(self, **kwargs):
        from bluebottle.assignments.models import Applicant
        source_states = [
            ApplicantTransitions.values.new,
            ApplicantTransitions.values.accepted,
            ApplicantTransitions.values.active,
        ]
        for member in self.instance.contributions.instance_of(Applicant).filter(status__in=source_states):
            member.activity = self.instance
            member.transitions.succeed()
            member.save()

    @transition(
        field='status',
        source=[values.closed],
        target=values.succeeded,
        permissions=[ActivityTransitions.is_system],
        messages=[AssignmentCompletedMessage]
    )
    def reopen_and_succeed(self, **kwargs):
        states = [
            ApplicantTransitions.values.new,
            ApplicantTransitions.values.closed,
            ApplicantTransitions.values.accepted,
            ApplicantTransitions.values.active,
            ApplicantTransitions.values.succeeded
        ]
        for member in self.instance.contributions.filter(status__in=states):
            member.activity = self.instance
            member.transitions.succeed()
            member.save()
        self.instance.review_transitions.organizer_succeed()

    @transition(
        field='status',
        source=[values.running, values.open, values.succeeded],
        target=values.closed,
        permissions=[ActivityTransitions.is_system],
        messages=[AssignmentClosedMessage]
    )
    def close(self, **kwargs):
        for member in self.instance.accepted_applicants:
            member.transitions.close()
            member.save()
        self.instance.review_transitions.organizer_close()

    @transition(
        field='status',
        source=[values.open, values.running, values.full],
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

    @transition(
        source=values.in_review,
        target=values.open,
        permissions=[ActivityTransitions.can_approve]
    )
    def reviewed(self):
        pass


class ApplicantTransitions(ContributionTransitions):
    class values(ContributionTransitions.values):
        accepted = ChoiceItem('accepted', _('accepted'))
        rejected = ChoiceItem('rejected', _('rejected'))
        withdrawn = ChoiceItem('withdrawn', _('withdrawn'))
        active = ChoiceItem('attending', _('attending'))

    default = ContributionTransitions.values.new

    def assignment_is_open(self):
        if self.instance.activity.status != ActivityTransitions.values.open:
            return _('The event is not open')

    def assignment_is_open_or_full(self):
        if self.instance.activity.status not in [
            ActivityTransitions.values.open,
            AssignmentTransitions.values.full
        ]:
            return _('The event is not open')

    @transition(
        source=[ContributionTransitions.values.new],
        target=ContributionTransitions.values.new,
        messages=[AssignmentApplicationMessage]
    )
    def initiate(self):
        pass

    @transition(
        field='status',
        source=[values.new, values.rejected],
        target=values.accepted,
        conditions=[assignment_is_open],
        permissions=[ContributionTransitions.is_activity_manager],
        messages=[ApplicantAcceptedMessage]
    )
    def accept(self):
        pass

    @transition(
        field='status',
        source=[values.new, values.accepted],
        target=values.rejected,
        permissions=[ContributionTransitions.is_activity_manager],
        messages=[ApplicantRejectedMessage]
    )
    def reject(self):
        unfollow(self.instance.user, self.instance.activity)

    @transition(
        field='status',
        source=[values.new, values.accepted],
        target=values.withdrawn,
        conditions=[assignment_is_open_or_full],
        permissions=[ContributionTransitions.is_user]
    )
    def withdraw(self):
        unfollow(self.instance.user, self.instance.activity)

    @transition(
        source=[values.withdrawn, values.closed],
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
        source='*',
        target=values.succeeded,
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def succeed(self):
        follow(self.instance.user, self.instance.activity)
        if not self.instance.time_spent:
            self.instance.time_spent = self.instance.activity.duration + (self.instance.activity.preparation or 0)

    @transition(
        field='status',
        source=[values.succeeded, values.accepted, values.active],
        target=values.failed,
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def fail(self):
        unfollow(self.instance.user, self.instance.activity)
        self.instance.time_spent = None

    @transition(
        field='status',
        source='*',
        target=values.closed,
        permissions=[ContributionTransitions.is_activity_manager]
    )
    def close(self):
        unfollow(self.instance.user, self.instance.activity)
        self.instance.time_spent = None
