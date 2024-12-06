from bluebottle.events.models import Event
from bluebottle.fsm.state import ModelStateMachine, register, Transition, State, EmptyState
from django.utils.translation import gettext_lazy as _


@register(Event)
class EventStateMachine(ModelStateMachine):

    draft = State(
        _('Draft'),
        'draft',
        _('Draft'),
    )

    published = State(
        _('Published'),
        'published',
        _('Published'),
    )

    initiate = Transition(
        EmptyState(),
        draft,
        name=_('Initiate'),
        description=_('The event is initiated.'),
    )

    publish = Transition(
        draft,
        published,
        name=_('Publish'),
        description=_('Publish the event.'),
    )
