from django.utils import timezone

from bluebottle.assignments.effects import SetTimeSpent, ClearTimeSpent
from bluebottle.assignments.messages import (
    AssignmentExpiredMessage, AssignmentApplicationMessage,
    ApplicantAcceptedMessage, ApplicantRejectedMessage, AssignmentCompletedMessage,
    AssignmentRejectedMessage, AssignmentCancelledMessage
)
from bluebottle.follow.effects import UnFollowActivityEffect, FollowActivityEffect
from bluebottle.notifications.effects import NotificationEffect
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.state import State, Transition, EmptyState


class AssignmentStateMachine(ActivityStateMachine):
    model = Assignment

    running = State(
        _('running'),
        'running',
        _('The task is taking place and people can\'t apply any more.')
    )
    full = State(
        _('full'),
        'full',
        _('The number of people needed is reached and people can\'t apply any more.')
    )

    def should_finish(self):
        """end date has passed"""
        return self.instance.end and self.instance.end < timezone.now()

    def should_start(self):
        """start date has passed"""
        return self.instance.start and self.instance.start < timezone.now() and not self.should_finish()

    def has_deadline(self):
        """has a deadline"""
        return self.instance.end_date_type == 'deadline'

    def is_on_date(self):
        """takes place on a set date"""
        return self.instance.end_date_type == 'on_date'

    def should_open(self):
        """registration deadline is in the future"""
        return self.instance.start and self.instance.start >= timezone.now() and not self.should_finish()

    def has_accepted_applicants(self):
        """there are accepted applicants"""
        return len(self.instance.accepted_applicants) > 0

    def has_no_accepted_applicants(self):
        """there are no accepted applicants"""
        return len(self.instance.accepted_applicants) == 0

    def has_new_or_accepted_applicants(self):
        """there are accepted applicants"""
        return len(self.instance.accepted_applicants) > 0 or len(self.instance.new_applicants) > 0

    def has_no_new_or_accepted_applicants(self):
        """there are no accepted applicants"""
        return len(self.instance.accepted_applicants) == 0 and len(self.instance.new_applicants) == 0

    def is_not_full(self):
        """the task is not full"""
        return self.instance.capacity > len(self.instance.accepted_applicants)

    def is_full(self):
        """the task is full"""
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
        name=_('Fill'),
        description=_(
            "People can no longer apply. Triggered when the number of accepted people "
            "equals the number of people needed."
        ),
    )

    auto_approve = Transition(
        [
            ActivityStateMachine.submitted,
            ActivityStateMachine.rejected
        ],
        ActivityStateMachine.open,
        name=_('Approve'),
        automatic=True,
        description=_(
            "The task will be visible in the frontend and people can apply to "
            "the task."
        ),
        effects=[
            RelatedTransitionEffect('organizer', 'succeed'),
            RelatedTransitionEffect('applicants', 'reset'),
            TransitionEffect(
                'expire',
                conditions=[should_finish, has_no_accepted_applicants]
            ),
        ]
    )

    reject = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
            ActivityStateMachine.submitted
        ],
        ActivityStateMachine.rejected,
        name=_('Reject'),
        description=_(
            'Reject in case this task doesn\'t fit your program or the rules of the game. '
            'The activity owner will not be able to edit the task and it won\'t show up on '
            'the search page in the front end. The task will still be available in the '
            'back office and appear in your reporting.'
        ),
        automatic=False,
        permission=ActivityStateMachine.is_staff,
        effects=[
            RelatedTransitionEffect('organizer', 'fail'),
            NotificationEffect(AssignmentRejectedMessage),
        ]
    )

    cancel = Transition(
        [
            full,
            running,
            ActivityStateMachine.succeeded,
            ActivityStateMachine.open,
        ],
        ActivityStateMachine.cancelled,
        name=_('Cancel'),
        description=_(
            'Cancel if the task will not be executed. The activity manager will not be able '
            'to edit the task and it won\'t show up on the search page in the front end. The '
            'task will still be available in the back office and appear in your reporting.'
        ),
        automatic=False,
        effects=[
            RelatedTransitionEffect('organizer', 'fail'),
            RelatedTransitionEffect('accepted_applicants', 'fail'),
            NotificationEffect(AssignmentCancelledMessage),
        ]
    )

    expire = Transition(
        [
            ActivityStateMachine.submitted,
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded
        ],
        ActivityStateMachine.cancelled,
        name=_("Expire"),
        description=_("The tasks didn\'t have any applicants before the deadline and is cancelled."),
        effects=[
            NotificationEffect(AssignmentExpiredMessage),
        ]
    )

    reopen = Transition(
        full,
        ActivityStateMachine.open,
        name=_('Reopen'),
        description=_(
            'People can apply to the task again. Triggered when the number of accepted people '
            'become less than the number of people needed.'
        ),
        automatic=True
    )

    reschedule = Transition(
        [
            ActivityStateMachine.cancelled,
            ActivityStateMachine.succeeded
        ],
        ActivityStateMachine.open,
        name=_('Reschedule'),
        description=_("Reschedule the activity for new sign-ups. "
                      "Triggered by a changing to a future date."),
        automatic=True,
        effects=[
            RelatedTransitionEffect('accepted_applicants', 'reaccept'),
        ]


    )

    succeed = Transition(
        [
            ActivityStateMachine.open,
            full,
            running,
            ActivityStateMachine.cancelled
        ],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        description=_(
            'The task ends and the contributions are counted. Triggered when the task date passes.'
        ),
        automatic=True,
        effects=[
            RelatedTransitionEffect('accepted_applicants', 'succeed'),
            RelatedTransitionEffect('new_applicants', 'succeed'),
            NotificationEffect(AssignmentCompletedMessage)
        ]
    )

    expire = Transition(
        ActivityStateMachine.open,
        ActivityStateMachine.cancelled,
        name=_('Expire'),
        description=_(
            "The task didn't have any applicants before the deadline to apply and is cancelled."
        ),
        automatic=True,
        effects=[
            RelatedTransitionEffect('organizer', 'fail'),
            NotificationEffect(AssignmentExpiredMessage),
        ]
    )

    restore = Transition(
        [
            ActivityStateMachine.rejected,
            ActivityStateMachine.cancelled,
            ActivityStateMachine.deleted,
        ],
        ActivityStateMachine.needs_work,
        name=_("Restore"),
        automatic=False,
        description=_("Restore a cancelled, rejected or deleted task."),
        effects=[
            RelatedTransitionEffect('organizer', 'reset'),
            RelatedTransitionEffect('accepted_applicants', 'fail')

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
        """task will be full"""
        activity = self.instance.activity
        return activity.capacity == len(activity.accepted_applicants) + 1

    def assignment_will_become_open(self):
        """task will not be full"""
        activity = self.instance.activity
        return activity.capacity == len(activity.accepted_applicants)

    def assignment_is_finished(self):
        """task is finished"""
        return self.instance.activity.end < timezone.now()

    def assignment_is_not_finished(self):
        "task is not finished"
        return not self.instance.activity.date < timezone.now()

    def assignment_will_be_empty(self):
        """task be empty"""
        return len(self.instance.activity.accepted_applicants) == 1

    def can_accept_applicants(self, user):
        """can accept applicants"""
        return user in [
            self.instance.activity.owner,
            self.instance.activity.initiative.activity_manager,
            self.instance.activity.initiative.owner
        ]

    def assignment_is_open(self):
        """task is open"""
        return self.instance.activity.status == ActivityStateMachine.open.value

    initiate = Transition(
        EmptyState(),
        ContributionStateMachine.new,
        name=_('Initiate'),
        description=_("User applied to join the task."),
        effects=[
            NotificationEffect(AssignmentApplicationMessage),
            FollowActivityEffect,
            TransitionEffect('succeed', conditions=[assignment_is_finished])
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

    reaccept = Transition(
        ContributionStateMachine.succeeded,
        accepted,
        name=_('Accept'),
        description=_("Applicant was accepted."),
        automatic=True,
        effects=[
            RelatedTransitionEffect('activity', 'lock', conditions=[assignment_will_become_full]),
            ClearTimeSpent,
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
        hide_from_admin=True,
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
        description=_("Applicant re-applies for the task after previously withdrawing."),
        automatic=False,
        conditions=[assignment_is_open],
        permission=ContributionStateMachine.is_user,
        effects=[
            FollowActivityEffect,
            NotificationEffect(AssignmentApplicationMessage)
        ]
    )

    activate = Transition(
        [
            accepted,
            # ContributionStateMachine.new
        ],
        active,
        name=_('Activate'),
        description=_("Applicant starts to execute the task."),
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
        description=_("Applicant successfully completed the task."),
        automatic=True,
        effects=[
            SetTimeSpent
        ]
    )

    mark_absent = Transition(
        ContributionStateMachine.succeeded,
        no_show,
        name=_('Mark absent'),
        description=_("Applicant did not contribute to the task and is marked absent."),
        automatic=False,
        permission=is_activity_owner,
        effects=[
            ClearTimeSpent,
            RelatedTransitionEffect(
                'activity', 'cancel',
                conditions=[assignment_is_finished, assignment_will_be_empty]
            ),
            UnFollowActivityEffect
        ]
    )
    mark_present = Transition(
        no_show,
        ContributionStateMachine.succeeded,
        name=_('Mark present'),
        description=_("Applicant did contribute to the task, after first been marked absent."),
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

    reset = Transition(
        [
            ContributionStateMachine.succeeded,
            accepted,
            ContributionStateMachine.failed,
        ],
        ContributionStateMachine.new,
        name=_('Reset'),
        description=_("The applicant is reset to new after being successful or failed."),
        effects=[ClearTimeSpent]
    )
