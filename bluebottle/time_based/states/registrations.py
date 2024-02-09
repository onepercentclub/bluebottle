from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import (
    register, State, Transition, EmptyState, ModelStateMachine
)
from bluebottle.time_based.models import (
    DeadlineRegistration, )


class RegistrationStateMachine(ModelStateMachine):
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
        _("This person is not selected for the activity.")
    )

    def can_accept_registration(self, user):
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

    initiate = Transition(
        EmptyState(),
        new,
        name=_('Initiate'),
        description=_(
            'The registration was created.'
        ),
    )

    auto_accept = Transition(
        new,
        accepted,
        name=_('Accept'),
        description=_("Automatically accept this person as a participant to the activity."),
        passed_label=_('accepted'),
        automatic=True,
    )

    accept = Transition(
        [new, rejected],
        accepted,
        name=_('Accept'),
        description=_("Accept this person as a participant to the activity."),
        passed_label=_('accepted'),
        automatic=False,
        permission=can_accept_registration,
    )

    reject = Transition(
        [new, accepted],
        rejected,
        name=_('Reject'),
        description=_("Reject this person as a participant in the activity."),
        automatic=False,
        permission=can_accept_registration,
    )


@register(DeadlineRegistration)
class DeadlineRegistrationStateMachine(RegistrationStateMachine):
    pass
