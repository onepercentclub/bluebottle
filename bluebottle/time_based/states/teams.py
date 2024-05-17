from bluebottle.fsm.state import register
from bluebottle.time_based.models import TeamMember, Team
from bluebottle.time_based.states import RegistrationStateMachine


@register(Team)
class MemberStateMachine(RegistrationStateMachine):
    pass


@register(TeamMember)
class TeamMemberStateMachine(RegistrationStateMachine):
    pass
