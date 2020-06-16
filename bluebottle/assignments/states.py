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
        """end date has passed"""
        return self.instance.end and self.instance.end < timezone.now()

    def should_start(self):
        """start date has passed"""
        return self.instance.date and self.instance.date < timezone.now()

    def has_deadline(self):
        """has a deadline"""
        return self.instance.end_date_type == 'deadline'

    def is_on_date(self):
        """takes place on a set date"""
        return self.instance.end_date_type == 'on_date'

    def should_open(self):
        """start date is in the future"""
        return self.instance.date and self.instance.date > timezone.now()

    def has_accepted_applicants(self):
        """there are accepted applicants"""
        return len(self.instance.accepted_applicants) > 0

    def has_no_accepted_applicants(self):
        """there are no accepted applicants"""
        return len(self.instance.accepted_applicants) == 0

    def is_not_full(self):
        """the assignment is not full"""
        return self.instance.capacity > len(self.instance.accepted_applicants)

    def is_full(self):
        """the assignment is full"""
        return self.instance.capacity <= len(self.instance.accepted_applicants)

    start = Transition(
        [ActivityStateMachine.open, full],
        running,
        name=_('Start'),
        description=_("Start the activity."),
        automatic=True,
        effects=[
            RelatedTransitionEffect('accepted_applicants', 'activate'),
        ]
    )

    lock = Transition(
        [ActivityStateMachine.open],
        full,
        automatic=True,
        name=_('Lock'),
        description=_("The activity has reached its capacity and is locked for new applications."),
    )

    reopen = Transition(
        full,
        ActivityStateMachine.open,
        name=_('Reopen'),
        description=_("Reopen the activity for new sign-ups. "
                      "Triggered by a change in capacity or the number of applicants."),
        automatic=True,
        effects=[
            RelatedTransitionEffect('accepted_applicants', 'succeed'),
        ]
    )

    succeed = Transition(
        [ActivityStateMachine.open, full, running, ActivityStateMachine.closed],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        description=_("The activity was successfully completed."),
        automatic=True,
        effects=[
            RelatedTransitionEffect('accepted_applicants', 'succeed'),
            NotificationEffect(AssignmentCompletedMessage)
        ]
    )

    expire = Transition(
        ActivityStateMachine.open,
        ActivityStateMachine.closed,
        name=_('Expire'),
        description=_("The activity expired. There were no sign-ups before the deadline to apply."),
        automatic=True,
        effects=[
            NotificationEffect(AssignmentExpiredMessage),
        ]
    )


class ApplicantStateMachine(ContributionStateMachine):
    model = Applicant

    accepted = State(
        _('accepted'),
        'accepted',
        _('The applicant was accepted and will join the activity.')
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _("The applicant was rejected and will not join the activity.")
    )
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('The applicant withdrew and will no longer join the activity.')
    )
    no_show = State(
        _('no show'),
        'no_show',
        _('The applicant did not contribute to the activity.')
    )
    active = State(
        _('active'),
        'active',
        _('The applicant is currently working on the activity.')
    )

    def has_time_spent(self):
        """time spent is set"""
        return self.instance.time_spent

    def has_no_time_spent(self):
        """time spent is not set"""
        return not self.instance.time_spent

    def is_user(self, user):
        """is applicant"""
        return self.instance.user == user

    def is_activity_owner(self, user):
        """is activity manager or staff member"""
        return user.is_staff or self.instance.activity.owner == user

    def assignment_will_become_full(self):
        """assignment_will be full"""
        activity = self.instance.activity
        return activity.capacity == len(activity.accepted_applicants) + 1

    def assignment_will_become_open(self):
        """assignment_will not be full"""
        activity = self.instance.activity
        return activity.capacity == len(activity.accepted_applicants)

    def assignment_is_finished(self):
        """assignment_is finished"""
        return self.instance.activity.end < timezone.now()

    def assignment_is_not_finished(self):
        "assignment_is not finished"
        return not self.instance.activity.date < timezone.now()

    def assignment_will_be_empty(self):
        """assignment_will be empty"""
        return len(self.instance.activity.accepted_applicants) == 1

    def can_accept_applicants(self, user):
        """can accept applicants"""
        return user in [
            self.instance.activity.owner,
            self.instance.activity.initiative.activity_manager,
            self.instance.activity.initiative.owner
        ]

    def assignment_is_open(self):
        """assignment is open"""
        return self.instance.activity.status == ActivityStateMachine.open.value

    initiate = Transition(
        EmptyState(),
        ContributionStateMachine.new,
        name=_('Initiate'),
        description=_("User applied to join the assignment."),
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
        description=_("Applicant was accepted."),
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
        description=_("Applicant was rejected."),
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
        description=_("Applicant withdrew and will no longer join the activity."),
        automatic=False,
        permission=is_user,
        effects=[
            UnFollowActivityEffect
        ]
    )

    reapply = Transition(
        [
            withdrawn,
            ContributionStateMachine.failed
        ],
        ContributionStateMachine.new,
        name=_('Reapply'),
        description=_("Applicant re-applies for the assignment after previously withdrawing."),
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
        description=_("Applicant starts to execute the assignment."),
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
        description=_("Applicant successfully completed the assignment."),
        automatic=True,
        effects=[
            SetTimeSpent
        ]
    )

    mark_absent = Transition(
        ContributionStateMachine.succeeded,
        no_show,
        name=_('Mark absent'),
        description=_("Applicant did not contribute to the assignment and is marked absent."),
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
        description=_("Applicant did contribute to the assignment, after first been marked absent."),
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
