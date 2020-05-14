from bluebottle.assignments.effects import SetTimeSpent, ClearTimeSpent
from bluebottle.assignments.messages import AssignmentExpiredMessage, AssignmentApplicationMessage, \
    ApplicantAcceptedMessage, ApplicantRejectedMessage
from bluebottle.follow.effects import UnFollowActivityEffect, FollowActivityEffect
from bluebottle.notifications.effects import NotificationEffect
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.state import State, Transition, EmptyState


class AssignmentStateMachine(ActivityStateMachine):
    model = Assignment

    running = State(_('running'), 'running',
                    _('Activity is currently being execute, not accepting new contributions'))
    full = State(_('full'), 'full',
                 _('Activity is full, not accepting new contributions'))

    # reopen: Removed this transition

    start = Transition(
        [ActivityStateMachine.open, full],
        running,
        name=_('Start'),
        effects=[
            RelatedTransitionEffect('accepted_applicants', 'activate')
        ]
    )

    lock = Transition(
        [ActivityStateMachine.open],
        full,
        name=_('Lock')
    )

    reopen = Transition(
        [ActivityStateMachine.open, full],
        running,
        name=_('Start'),
        effects=[
            RelatedTransitionEffect('accepted_applicants', 'activate')
        ]
    )

    succeed = Transition(
        [ActivityStateMachine.open, full],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        effects=[
            RelatedTransitionEffect('active_applicants', 'succeed')
        ]
    )

    expire = Transition(
        [ActivityStateMachine.open, running, full],
        ActivityStateMachine.closed,
        name=_('Succeed'),
        effects=[
            NotificationEffect(AssignmentExpiredMessage)
        ]
    )


class ApplicantStateMachine(ContributionStateMachine):
    model = Applicant

    accepted = State(_('accepted'), 'accepted', _('accepted'))
    rejected = State(_('rejected'), 'rejected', _('rejected'))
    withdrawn = State(_('withdrawn'), 'withdrawn', _('withdrawn'))
    active = State(_('active'), 'active', _('active'))

    def can_accept_applicants(self, user):
        return user in [
            self.instance.activity.owner,
            self.instance.activity.initiative.activity_manager,
            self.instance.activity.initiative.owner
        ]

    def assignment_is_open(self):
        if self.instance.activity.status != ActivityStateMachine.open.value:
            return _('The assignment is not open')

    def assignment_is_open_or_full(self):
        if self.instance.activity.status in [
            ActivityStateMachine.open.value,
            AssignmentStateMachine.full.value
        ]:
            return _('The assignment is not open')

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
        conditions=[assignment_is_open],
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
        permission=can_accept_applicants,
        conditions=[assignment_is_open_or_full],
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
            ContributionStateMachine.new
        ],
        active,
        name=_('Activate'),
        automatic=True,
        conditions=[assignment_is_open_or_full],
    )

    succeed = Transition(
        [
            accepted,
            active,
            ContributionStateMachine.new
        ],
        active,
        name=_('Activate'),
        automatic=True,
        conditions=[assignment_is_open_or_full],
        effects=[
            SetTimeSpent
        ]
    )

    close = Transition(
        [
            accepted,
            ContributionStateMachine.new
        ],
        active,
        name=_('Activate'),
        automatic=True,
        conditions=[assignment_is_open_or_full],
        permission=can_accept_applicants,
        effects=[
            ClearTimeSpent
        ]
    )
