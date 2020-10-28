from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import (
    ActivityStateMachine, ContributionStateMachine, ContributionValueStateMachine
)
from bluebottle.time_based.models import (
    OnADateActivity, WithADeadlineActivity, OngoingActivity, Application, Duration
)
from bluebottle.fsm.state import register, State, Transition, EmptyState


class TimeBasedStateMachine(ActivityStateMachine):
    full = State(_('full'), 'full', _('The event is full, users can no longer apply.'))
    running = State(_('running'), 'running', _('The event is running, users can no longer apply.'))

    lock = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
            running
        ],
        full,
        name=_("Lock"),
        description=_(
            "People can no longer join the event. Triggered when the attendee limit is reached."
        )
    )

    reopen = Transition(
        [running, full],
        ActivityStateMachine.open,
        name=_("Reopen"),
        description=_(
            "People can join the event again. Triggered when the number of attendees become "
            "less than the attendee limit."
        )
    )

    succeed = Transition(
        [ActivityStateMachine.open, ActivityStateMachine.cancelled, full, running],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
    )

    start = Transition(
        [
            ActivityStateMachine.open,
            full
        ],
        running,
        name=_("Start"),
        description=_("Start the event.")
    )


@register(OnADateActivity)
class OnADateStateMachine(TimeBasedStateMachine):
    reschedule = Transition(
        [
            TimeBasedStateMachine.running,
            ActivityStateMachine.cancelled,
            ActivityStateMachine.succeeded
        ],
        ActivityStateMachine.open,
        name=_("Reschedule"),
        description=_("People can join the event again, because the date has changed."),
    )


@register(WithADeadlineActivity)
class WithADeadlineStateMachine(TimeBasedStateMachine):

    reschedule = Transition(
        [
            ActivityStateMachine.cancelled,
            ActivityStateMachine.succeeded
        ],
        ActivityStateMachine.open,
        name=_("Reschedule"),
        description=_("People can join the event again, because the date has changed."),
    )


@register(OngoingActivity)
class OngoingStateMachine(TimeBasedStateMachine):
    pass


@register(Application)
class ApplicationStateMachine(ContributionStateMachine):
    accepted = State(
        _('accepted'),
        'accepted',
        _('The application was accepted and will join the activity.')
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _("The application was rejected and will not join the activity.")
    )
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('The application withdrew and will no longer join the activity.')
    )
    no_show = State(
        _('no show'),
        'no_show',
        _('The application did not contribute to the activity.')
    )

    def is_user(self, user):
        """is application"""
        return self.instance.user == user

    def can_accept_application(self, user):
        """can accept application"""
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
    )

    accept = Transition(
        [
            ContributionStateMachine.new,
            rejected
        ],
        accepted,
        name=_('Accept'),
        description=_("Application was accepted."),
        automatic=False,
        permission=can_accept_application,
    )

    reject = Transition(
        [
            ContributionStateMachine.new,
            accepted
        ],
        rejected,
        name=_('Reject'),
        description=_("Application was rejected."),
        automatic=False,
        permission=can_accept_application,
    )

    withdraw = Transition(
        [
            ContributionStateMachine.new,
            accepted
        ],
        withdrawn,
        name=_('Withdraw'),
        description=_("User withdrew and will no longer join the activity."),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    reapply = Transition(
        withdrawn,
        ContributionStateMachine.new,
        name=_('Reapply'),
        description=_("User re-applies for the task after previously withdrawing."),
        automatic=False,
        conditions=[assignment_is_open],
        permission=ContributionStateMachine.is_user,
    )

    mark_absent = Transition(
        ContributionStateMachine.succeeded,
        no_show,
        name=_('Mark absent'),
        description=_("User did not contribute to the task and is marked absent."),
        automatic=False,
        permission=can_accept_application,
    )
    mark_present = Transition(
        no_show,
        ContributionStateMachine.succeeded,
        name=_('Mark present'),
        description=_("Application did contribute to the task, after first been marked absent."),
        automatic=False,
        permission=can_accept_application,
    )


@register(Duration)
class DurationStateMachine(ContributionValueStateMachine):
    pass
