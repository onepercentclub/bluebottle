from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import (
    register, Transition
)
from bluebottle.time_based.models import (
    DeadlineParticipant,
)
from bluebottle.time_based.states import ParticipantStateMachine


@register(DeadlineParticipant)
class DeadlineParticipantStateMachine(ParticipantStateMachine):

    succeed = Transition(
        [
            ParticipantStateMachine.accepted,
            ParticipantStateMachine.new,
            ParticipantStateMachine.failed,
            ParticipantStateMachine.withdrawn,
            ParticipantStateMachine.cancelled,
        ],
        ParticipantStateMachine.succeeded,
        name=_('Succeed'),
        automatic=False,
        description=_("This participant hass completed their contribution."),
    )
