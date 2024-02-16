from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import (
    ContributorStateMachine
)
from bluebottle.fsm.state import (
    register, State, Transition, EmptyState
)
from bluebottle.time_based.models import (
    DateParticipant, PeriodParticipant, )
from bluebottle.time_based.models import (
    DeadlineParticipant,
)
from bluebottle.time_based.states.states import TimeBasedStateMachine


class ParticipantStateMachine(ContributorStateMachine):
    new = State(
        _('pending'),
        'new',
        _("This person has applied and must be reviewed.")
    )
    accepted = State(
        _('participating'),
        'accepted',
        _('This person takes part in the activity.')
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _("This person's contribution is rejected and the spent hours are reset to zero.")
    )
    removed = State(
        _('removed'),
        'removed',
        _("This person's contribution is removed and the spent hours are reset to zero.")
    )
    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _('This person has withdrawn. Spent hours are retained.')
    )
    cancelled = State(
        _('cancelled'),
        'cancelled',
        _("The activity has been cancelled. This person's contribution "
          "is removed and the spent hours are reset to zero.")
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _('This person hast successfully contributed.')
    )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user

    def can_accept_participant(self, user):
        """can accept participant"""
        return (
            user in [
                self.instance.activity.owner,
                self.instance.activity.initiative.owner
            ] or
            (self.instance.team and self.instance.team.owner == user) or
            user.is_staff or
            user in self.instance.activity.initiative.activity_managers.all()
        )

    def activity_is_open(self):
        """task is open"""
        return self.instance.activity.status in (
            TimeBasedStateMachine.open.value,
            TimeBasedStateMachine.full.value
        )

    initiate = Transition(
        EmptyState(),
        ContributorStateMachine.new,
        name=_('Initiate'),
        description=_("User applied to join the task."),
    )

    accept = Transition(
        [
            ContributorStateMachine.new,
            withdrawn,
            rejected
        ],
        accepted,
        name=_('Accept'),
        description=_("Accept this person as a participant to the Activity."),
        passed_label=_('accepted'),
        automatic=False,
        permission=can_accept_participant,
    )

    add = Transition(
        [
            ContributorStateMachine.new
        ],
        accepted,
        name=_('Add'),
        description=_("Add this person as a participant to the activity."),
        automatic=True
    )

    reject = Transition(
        [
            ContributorStateMachine.new,
            accepted
        ],
        rejected,
        name=_('Reject'),
        description=_("Reject this person as a participant in the activity."),
        automatic=True,
        permission=can_accept_participant,
    )

    succeed = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.failed,
            rejected,
            accepted
        ],
        succeeded,
        name=_('Succeed'),
        description=_("This participant has completed their contribution."),
        automatic=False,
        permission=can_accept_participant,
    )

    remove = Transition(
        [
            accepted,
            succeeded
        ],
        removed,
        name=_('Remove'),
        passed_label=_('removed'),
        description=_("Remove this person as a participant from the activity."),
        automatic=False,
        permission=can_accept_participant,
    )

    withdraw = Transition(
        [
            ContributorStateMachine.new,
            succeeded,
            accepted
        ],
        withdrawn,
        name=_('Withdraw'),
        passed_label=_('withdrawn'),
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
        passed_label=_('reapplied'),
        description=_("User re-applies for the activity after previously withdrawing."),
        description_front_end=_("Do you want to sign up for this activity again?"),
        automatic=False,
        conditions=[activity_is_open],
        permission=is_user,
    )

    cancel = Transition(
        [
            ContributorStateMachine.new,
            accepted,
            succeeded
        ],
        cancelled,
        name=_('Cancel'),
        passed_label=_('cancelled'),
        description=_("Cancel the participant, because the activity was cancelled."),
        automatic=True,
    )


@register(DateParticipant)
class DateParticipantStateMachine(ParticipantStateMachine):
    pass


@register(PeriodParticipant)
class PeriodParticipantStateMachine(ParticipantStateMachine):
    def is_not_team(self):
        return not self.instance.team

    stopped = State(
        _('stopped'),
        'stopped',
        _('The participant (temporarily) stopped. Contributions will no longer be created.')
    )

    stop = Transition(
        ParticipantStateMachine.accepted,
        stopped,
        name=_('Stop'),
        permission=ParticipantStateMachine.can_accept_participant,
        description=_("Participant stopped contributing."),
        automatic=False,
        conditions=[ParticipantStateMachine.activity_is_open, is_not_team]
    )

    start = Transition(
        stopped,
        ParticipantStateMachine.accepted,
        name=_('Start'),
        permission=ParticipantStateMachine.can_accept_participant,
        description=_("Participant started contributing again."),
        automatic=False,
    )


@register(DeadlineParticipant)
class DeadlineParticipantStateMachine(ParticipantStateMachine):
    reject = None
