from django.utils import timezone

from bluebottle.assignments.effects import SetTimeSpent, ClearTimeSpent
from bluebottle.assignments.messages import AssignmentExpiredMessage, AssignmentApplicationMessage, \
    ApplicantAcceptedMessage, ApplicantRejectedMessage, AssignmentCompletedMessage
from bluebottle.follow.effects import UnFollowActivityEffect, FollowActivityEffect
from bluebottle.notifications.effects import NotificationEffect
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.state import State, Transition, EmptyState


class AssignmentStateMachine(ActivityStateMachine):
    model = Assignment

    running = State(_('running'), 'running',
                    _('Activity is currently being execute, not accepting new contributions'))
    full = State(_('full'), 'full',
                 _('Activity is full, not accepting new contributions'))

    def should_finish(self):
        # FIXME
        return self.instance.end and self.instance.end < timezone.now()

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
        (ActivityStateMachine.succeeded, ActivityStateMachine.closed, full, ),
        ActivityStateMachine.open,
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
        [ActivityStateMachine.open, running, full],
        ActivityStateMachine.closed,
        name=_('Expire'),
        automatic=True,
        effects=[
            NotificationEffect(AssignmentExpiredMessage),
        ]
    )


class ApplicantStateMachine(ContributionStateMachine):
    model = Applicant

    accepted = State(_('accepted'), 'accepted', _('accepted'))
    rejected = State(_('rejected'), 'rejected', _('rejected'))
    withdrawn = State(_('withdrawn'), 'withdrawn', _('withdrawn'))
    no_show = State(_('no show'), 'no_show', _('no_show'))
    active = State(_('active'), 'active', _('active'))

    def has_time_spent(self):
        return self.instance.time_spent

    def has_no_time_spent(self):
        return not self.instance.time_spent

    def is_user(self, user):
        return self.instance.user == user

    def is_activity_owner(self, user):
        return user.is_staff or self.instance.activity.owner == user

    def assignment_will_become_full(self):
        "assignment_will be full"
        activity = self.instance.activity
        return activity.capacity == len(activity.accepted_applicants) + 1

    def assignment_will_become_open(self):
        "assignment_will not be full"
        activity = self.instance.activity
        return activity.capacity == len(activity.accepted_applicants)

    def assignment_is_finished(self):
        "assignment_is finished"
        return self.instance.activity.end < timezone.now()

    def assignment_is_not_finished(self):
        "assignment_is not finished"
        return not self.instance.activity.date < timezone.now()

    def assignment_will_be_empty(self):
        "assignment_will be empty"
        return len(self.instance.activity.accepted_applicants) == 1

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
        effects=[
            TransitionEffect('succeed', conditions=[assignment_is_finished]),
            RelatedTransitionEffect('activity', 'lock', conditions=[assignment_will_become_full]),
            RelatedTransitionEffect(
                'activity',
                'succeed',
                conditions=[assignment_is_finished]
            ),
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
            RelatedTransitionEffect('activity', 'reopen'),
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
        permission=is_user,
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

    mark_absent = Transition(
        ContributionStateMachine.succeeded,
        no_show,
        name=_('Mark absent'),
        automatic=False,
        permission=is_activity_owner,
        effects=[
            ClearTimeSpent,
            RelatedTransitionEffect(
                'activity', 'close',
                conditions=[assignment_is_finished, assignment_will_be_empty]
            ),
            UnFollowActivityEffect
        ]
    )
    mark_present = Transition(
        no_show,
        ContributionStateMachine.succeeded,
        name=_('Mark present'),
        automatic=False,
        permission=is_activity_owner,
        effects=[
            SetTimeSpent,
            RelatedTransitionEffect(
                'activity', 'succeed',
                conditions=[assignment_is_finished]
            ),
            FollowActivityEffect
        ]
    )
