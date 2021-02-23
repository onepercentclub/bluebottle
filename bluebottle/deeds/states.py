from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributorStateMachine
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.fsm.state import register, State, Transition


@register(Deed)
class DeedStateMachine(ActivityStateMachine):
    running = State(
        _('running'),
        'running',
        _('The activity is taking place and people can\'t participate any more.')
    )

    start = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded,
        ],
        running,
        name=_("Start"),
        description=_("Start the activity.")
    )

    restart = Transition(
        [
            ActivityStateMachine.expired,
            ActivityStateMachine.succeeded,
        ],
        running,
        name=_("Start"),
        description=_("Restart the activity.")
    )

    reopen = Transition(
        [
            running,
            ActivityStateMachine.expired,
            ActivityStateMachine.succeeded,
        ],
        ActivityStateMachine.open,
        name=_("Reopen"),
        description=_("Reopen the activity.")
    )


@register(DeedParticipant)
class ParticipantStateMachine(ContributorStateMachine):
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('This person has withdrawn. Spent hours are retained.')
    )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user or user.is_staff

    def activity_is_open(self):
        """task is open"""
        return self.instance.activity.status in (
            DeedStateMachine.open.value,
            DeedStateMachine.running.value,
        )

    succeed = Transition(
        ContributorStateMachine.new,
        ContributorStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
    )

    withdraw = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.new
        ],
        withdrawn,
        name=_('Withdraw'),
        description=_("Stop your participation in the activity. "
                      "Any hours spent will be kept, but no new hours will be allocated."),
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
        conditions=[activity_is_open],
        permission=is_user,
    )
