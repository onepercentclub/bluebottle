from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine
from bluebottle.time_based.models import OnADateActivity, WithADeadlineActivity, OngoingActivity
from bluebottle.fsm.state import register, State, Transition


class TimeBasedStateMachine(ActivityStateMachine):
    full = State(_('full'), 'full', _('The event is full, users can no longer apply.'))

    lock = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded
        ],
        full,
        name=_("Lock"),
        description=_(
            "People can no longer join the event. Triggered when the attendee limit is reached."
        )
    )

    reopen = Transition(
        full,
        ActivityStateMachine.open,
        name=_("Reopen"),
        description=_(
            "People can join the event again. Triggered when the number of attendees become "
            "less than the attendee limit."
        )
    )


@register(OnADateActivity)
class OnADateStateMachine(TimeBasedStateMachine):
    running = State(
        _('running'),
        'running',
        _('The event is taking place and people can\'t join any more.')
    )

    start = Transition(
        [
            ActivityStateMachine.open,
            TimeBasedStateMachine.full
        ],
        running,
        name=_("Start"),
        description=_("Start the event.")
    )

    reschedule = Transition(
        [
            running,
            ActivityStateMachine.cancelled,
            ActivityStateMachine.succeeded
        ],
        ActivityStateMachine.open,
        name=_("Reschedule"),
        description=_("People can join the event again, because the date has changed."),
    )


@register(WithADeadlineActivity)
class WithADeadlineStateMachine(TimeBasedStateMachine):
    pass


@register(OngoingActivity)
class OngoingStateMachine(TimeBasedStateMachine):
    pass
