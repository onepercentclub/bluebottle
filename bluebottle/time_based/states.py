from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import (
    ActivityStateMachine, ContributorStateMachine, ContributionValueStateMachine
)
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, Duration,
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
        [
            ActivityStateMachine.open,
            ActivityStateMachine.cancelled,
            full,
            running
        ],
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


@register(DateActivity)
class DateStateMachine(TimeBasedStateMachine):
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


@register(PeriodActivity)
class PeriodStateMachine(TimeBasedStateMachine):

    reschedule = Transition(
        [
            ActivityStateMachine.cancelled,
            ActivityStateMachine.succeeded
        ],
        ActivityStateMachine.open,
        name=_("Reschedule"),
        description=_("People can join the event again, because the date has changed."),
    )


class ParticipantStateMachine(ContributorStateMachine):
    accepted = State(
        _('accepted'),
        'accepted',
        _('The participant was accepted and will join the activity.')
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _("The participant was rejected and will not join the activity.")
    )
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('The participant withdrew and will no longer join the activity.')
    )
    no_show = State(
        _('no show'),
        'no_show',
        _('The participant did not contribute to the activity.')
    )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user

    def can_accept_participant(self, user):
        """can accept participant"""
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
        description=_("Participant was accepted."),
        automatic=False,
        permission=can_accept_participant,
    )

    reject = Transition(
        [
            ContributorStateMachine.new,
            accepted
        ],
        rejected,
        name=_('Reject'),
        description=_("Participant was rejected."),
        automatic=False,
        permission=can_accept_participant,
    )

    withdraw = Transition(
        [
            ContributorStateMachine.new,
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
        ContributorStateMachine.new,
        name=_('Reapply'),
        description=_("User re-applies for the task after previously withdrawing."),
        automatic=False,
        conditions=[assignment_is_open],
        permission=ContributorStateMachine.is_user,
    )

    mark_absent = Transition(
        ContributorStateMachine.succeeded,
        no_show,
        name=_('Mark absent'),
        description=_("User did not contribute to the task and is marked absent."),
        automatic=False,
        permission=can_accept_participant,
    )
    mark_present = Transition(
        no_show,
        ContributorStateMachine.succeeded,
        name=_('Mark present'),
        description=_("Participant did contribute to the task, after first been marked absent."),
        automatic=False,
        permission=can_accept_participant,
    )


@register(DateParticipant)
class DateParticipantStateMachine(ParticipantStateMachine):
    pass


@register(PeriodParticipant)
class PeriodParticipantStateMachine(ParticipantStateMachine):
    stopped = State(
        _('stopped'),
        'stopped',
        _('The participant (temporarily) stopped. Durations will no longer be created.')
    )

    stop = Transition(
        ParticipantStateMachine.accepted,
        stopped,
        name=_('Stop'),
        description=_("Participant stopped contributing."),
        automatic=False,
    )

    start = Transition(
        stopped,
        ParticipantStateMachine.accepted,
        name=_('Start'),
        description=_("Participant started contributing again."),
        automatic=False,
    )


@register(Duration)
class DurationStateMachine(ContributionValueStateMachine):
    pass
