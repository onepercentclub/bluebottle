from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import (
    EmptyState,
    ModelStateMachine,
    State,
    Transition,
    register,
)
from bluebottle.voting.models import Poll


@register(Poll)
class PollStateMachine(ModelStateMachine):
    draft = State(
        _('Draft'),
        'draft',
        _('The poll is being prepared and is not yet open for voting.'),
    )
    open = State(
        _('Open'),
        'open',
        _('The poll is open and people can vote.'),
    )
    closed = State(
        _('Closed'),
        'closed',
        _('The poll is closed and voting is no longer possible.'),
    )
    cancelled = State(
        _('Cancelled'),
        'cancelled',
        _('The poll has been cancelled.'),
    )

    initiate = Transition(
        EmptyState(),
        draft,
        name=_('Initiate'),
        description=_('The poll was created.'),
    )

    publish = Transition(
        draft,
        open,
        name=_('Publish'),
        description=_('Open the poll for voting.'),
        automatic=False,
    )

    close = Transition(
        open,
        closed,
        name=_('Close'),
        description=_('Close the poll so voting is no longer possible.'),
        automatic=True,
    )

    cancel = Transition(
        [draft, open],
        cancelled,
        name=_('Cancel'),
        description=_('Cancel the poll.'),
        automatic=False,
    )

    reopen = Transition(
        [closed, cancelled],
        open,
        name=_('Reopen'),
        description=_('Reopen the poll for voting.'),
        automatic=False,
    )
