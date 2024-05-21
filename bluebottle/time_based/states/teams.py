from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import register, ModelStateMachine, Transition, EmptyState, State
from bluebottle.time_based.models import TeamMember, Team


@register(Team)
class TeamStateMachine(ModelStateMachine):
    new = State(
        _('new'),
        'new',
        _("This team is new.")
    )

    accepted = State(
        _('accepted'),
        'accepted',
        _("This team has been accepted.")
    )

    initiate = Transition(
        EmptyState(),
        new,
        name=_('Initiate'),
        description=_(
            'The team was created.'
        ),
    )

    accept = Transition(
        new,
        accepted,
        name=_('Accept'),
        description=_(
            'The team has been accepted.'
        ),
    )


@register(TeamMember)
class TeamMemberStateMachine(ModelStateMachine):
    new = State(
        _('new'),
        'new',
        _("This team member is new.")
    )

    initiate = Transition(
        EmptyState(),
        new,
        name=_('Initiate'),
        description=_(
            'The team member joined.'
        ),
    )
