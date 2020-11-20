from bluebottle.assignments.models import Assignment, Applicant

from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributorStateMachine
from bluebottle.fsm.state import State, Transition, EmptyState, register


@register(Assignment)
class AssignmentStateMachine(ActivityStateMachine):

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

    start = Transition(
        [ActivityStateMachine.open, full],
        running,
        name=_('Start'),
        description=_("Start the activity."),
        automatic=True,
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
            'The task ends and the contributors are counted. Triggered when the task date passes.'
        ),
        automatic=True,
    )


@register(Applicant)
class ApplicantStateMachine(ContributorStateMachine):

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

    def is_user(self, user):
        """is applicant"""
        return self.instance.user == user

    def is_activity_owner(self, user):
        """is activity manager or staff member"""
        return user.is_staff or self.instance.activity.owner == user

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
        ContributorStateMachine.new,
        name=_('Initiate'),
        description=_("User applied to join the task."),
    )

    accept = Transition(
        [
            ContributorStateMachine.new,
            rejected
        ],
        accepted,
        name=_('Accept'),
        description=_("Applicant was accepted."),
        automatic=False,
        permission=can_accept_applicants,
    )

    reaccept = Transition(
        ContributorStateMachine.succeeded,
        accepted,
        name=_('Accept'),
        description=_("Applicant was accepted."),
        automatic=True,
    )

    reject = Transition(
        [
            ContributorStateMachine.new,
            accepted
        ],
        rejected,
        name=_('Reject'),
        description=_("Applicant was rejected."),
        automatic=False,
        permission=can_accept_applicants,
    )

    withdraw = Transition(
        [
            ContributorStateMachine.new,
            accepted
        ],
        withdrawn,
        name=_('Withdraw'),
        description=_("Applicant withdrew and will no longer join the activity."),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        [
            withdrawn,
            ContributorStateMachine.failed
        ],
        ContributorStateMachine.new,
        name=_('Reapply'),
        description=_("Applicant re-applies for the task after previously withdrawing."),
        automatic=False,
        conditions=[assignment_is_open],
        permission=ContributorStateMachine.is_user,
    )

    activate = Transition(
        [
            accepted,
            # ContributorStateMachine.new
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
            ContributorStateMachine.new
        ],
        ContributorStateMachine.succeeded,
        name=_('Succeed'),
        description=_("Applicant successfully completed the task."),
        automatic=True,
    )

    mark_absent = Transition(
        ContributorStateMachine.succeeded,
        no_show,
        name=_('Mark absent'),
        description=_("Applicant did not contribute to the task and is marked absent."),
        automatic=False,
        permission=is_activity_owner,
    )
    mark_present = Transition(
        no_show,
        ContributorStateMachine.succeeded,
        name=_('Mark present'),
        description=_("Applicant did contribute to the task, after first been marked absent."),
        automatic=False,
        permission=is_activity_owner,
    )

    reset = Transition(
        [
            ContributorStateMachine.succeeded,
            accepted,
            ContributorStateMachine.failed,
        ],
        ContributorStateMachine.new,
        name=_('Reset'),
        description=_("The applicant is reset to new after being successful or failed."),
    )
