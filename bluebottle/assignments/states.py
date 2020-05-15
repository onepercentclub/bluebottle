from django.utils import timezone

from bluebottle.assignments.effects import SetTimeSpent, ClearTimeSpent
from bluebottle.assignments.messages import AssignmentExpiredMessage, AssignmentApplicationMessage, \
    ApplicantAcceptedMessage, ApplicantRejectedMessage, AssignmentClosedMessage, AssignmentCompletedMessage
from bluebottle.follow.effects import UnFollowActivityEffect, FollowActivityEffect
from bluebottle.notifications.effects import NotificationEffect
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.state import State, Transition, EmptyState, AllStates


class AssignmentStateMachine(ActivityStateMachine):
    model = Assignment

    running = State(_('running'), 'running',
                    _('Activity is currently being execute, not accepting new contributions'))
    full = State(_('full'), 'full',
                 _('Activity is full, not accepting new contributions'))

    def should_finish(self):
        # FIXME
        return self.instance.end_date and self.instance.end_date < timezone.now()

    def should_start(self):
        # FIXME
        return self.instance.date and self.instance.date < timezone.now()

    def should_open(self):
        # FIXME
        return self.instance.date and self.instance.date > timezone.now()

    def has_accepted_applicants(self):
        "there are accepted applicants"
        return len(self.instance.accepted_applicants) > 0

    def has_no_accepted_applicants(self):
        "there are no accepted applicants"
        return len(self.instance.accepted_applicants) == 0

    def is_not_full(self):
        "the assignment is not full"
        return self.instance.capacity > len(self.instance.accepted_applicants)

    def is_full(self):
        "the assignment is full"
        return self.instance.capacity <= len(self.instance.accepted_applicants)

    start = Transition(
        [ActivityStateMachine.open, full],
        running,
        name=_('Start'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('accepted_applicants', 'activate')
        ]
    )

    lock = Transition(
        [ActivityStateMachine.open],
        full,
        automatic=True,
        name=_('Lock')
    )

    reopen = Transition(
        full,
        open,
        name=_('Reopen'),
        automatic=True,
    )

    succeed = Transition(
        [ActivityStateMachine.open, full, running],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('active_applicants', 'succeed'),
            NotificationEffect(AssignmentCompletedMessage)
        ]
    )

    expire = Transition(
        [ActivityStateMachine.open, running, full, running],
        ActivityStateMachine.closed,
        name=_('Expire'),
        automatic=True,
        effects=[
            NotificationEffect(AssignmentExpiredMessage)
        ]
    )

    close = Transition(
        AllStates(),
        ActivityStateMachine.closed,
        name=_('Close'),
        automatic=False,
        effects=[
            NotificationEffect(AssignmentClosedMessage),
            RelatedTransitionEffect('active_applicants', 'close'),
            RelatedTransitionEffect('organizer', 'close')
        ]
    )

    restore = Transition(
        ActivityStateMachine.closed,
        ActivityStateMachine.open,
        name=_('Restore'),
        automatic=False,
        effects=[
            RelatedTransitionEffect('active_applicants', 'reset'),
            RelatedTransitionEffect('organizer', 'succeed')
        ]
    )


class ApplicantStateMachine(ContributionStateMachine):
    model = Applicant

    accepted = State(_('accepted'), 'accepted', _('accepted'))
    rejected = State(_('rejected'), 'rejected', _('rejected'))
    withdrawn = State(_('withdrawn'), 'withdrawn', _('withdrawn'))
    active = State(_('active'), 'active', _('active'))

    def has_time_spent(self):
        return self.instance.time_spent

    def has_no_time_spent(self):
        return not self.instance.time_spent

    def can_accept_applicants(self, user):
        return user in [
            self.instance.activity.owner,
            self.instance.activity.initiative.activity_manager,
            self.instance.activity.initiative.owner
        ]

    def assignment_is_open(self):
        return self.instance.activity.status == ActivityStateMachine.open.value

    initiate = Transition(
        EmptyState(),
        ContributionStateMachine.new,
        name=_('Initiate'),
        effects=[
            NotificationEffect(AssignmentApplicationMessage),
            FollowActivityEffect
        ]
    )

    accept = Transition(
        [
            ContributionStateMachine.new,
            rejected
        ],
        accepted,
        name=_('Accept'),
        automatic=False,
        permission=can_accept_applicants,
        conditions=[assignment_is_open],
        effects=[
            NotificationEffect(ApplicantAcceptedMessage)
        ]
    )

    reject = Transition(
        [
            ContributionStateMachine.new,
            accepted
        ],
        rejected,
        name=_('Reject'),
        automatic=False,
        permission=can_accept_applicants,
        effects=[
            NotificationEffect(ApplicantRejectedMessage),
            UnFollowActivityEffect
        ]
    )

    withdraw = Transition(
        [
            ContributionStateMachine.new,
            accepted
        ],
        withdrawn,
        name=_('Withdraw'),
        automatic=False,
        effects=[
            UnFollowActivityEffect
        ]
    )

    reapply = Transition(
        [
            withdrawn,
            ContributionStateMachine.closed
        ],
        ContributionStateMachine.new,
        name=_('Reapply'),
        automatic=False,
        conditions=[assignment_is_open],
        permission=ContributionStateMachine.is_user,
        effects=[
            FollowActivityEffect
        ]
    )

    activate = Transition(
        [
            accepted,
            # ContributionStateMachine.new
        ],
        active,
        name=_('Activate'),
        automatic=True
    )

    succeed = Transition(
        [
            accepted,
            active,
            ContributionStateMachine.new
        ],
        ContributionStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
        effects=[
            SetTimeSpent
        ]
    )

    close = Transition(
        AllStates(),
        active,
        name=_('Activate'),
        automatic=True,
        permission=can_accept_applicants,
        effects=[
            ClearTimeSpent
        ]
    )
