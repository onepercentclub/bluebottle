from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import (
    register, State, Transition, EmptyState, ModelStateMachine
)
from bluebottle.time_based.models import (
    DeadlineRegistration,
    PeriodicRegistration, ScheduleRegistration, )


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
            user.is_superuser or
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


@register(ScheduleRegistration)
class ScheduleRegistrationStateMachine(RegistrationStateMachine):
    def can_schedule_registration(self, user):
        """can accept participant"""
        return self.instance.participants.count() > 0 and (
            user
            in [self.instance.activity.owner, self.instance.activity.initiative.owner]
            or user.is_superuser
            or user.is_staff
            or user in self.instance.activity.initiative.activity_managers.all()
        )

    scheduled = State(
        _("scheduled"),
        "scheduled",
        _("This person is assigned a slot for this activity."),
    )

    auto_schedule = Transition(
        [
            RegistrationStateMachine.new,
            RegistrationStateMachine.accepted,
            RegistrationStateMachine.rejected,
        ],
        scheduled,
        name=_("Reject"),
        description=_("Assign a slot to this participant"),
        automatic=True,
    )
    schedule = Transition(
        [
            RegistrationStateMachine.new,
            RegistrationStateMachine.accepted,
            RegistrationStateMachine.rejected,
        ],
        scheduled,
        name=_("Reject"),
        description=_("Assign a slot to this participant"),
        automatic=False,
        permission=can_schedule_registration,
    )


@register(PeriodicRegistration)
class PeriodicRegistrationStateMachine(RegistrationStateMachine):

    def is_user(self, user):
        """can accept participant"""
        return user == self.instance.user

    withdrawn = State(
        _('withdrawn'),
        'withdrawn',
        _("This person has withdrawn from the activity. Contributions are not counted.")
    )

    stopped = State(
        _('stopped'),
        'stopped',
        _("This person stopped contributing to this activity.")
    )

    withdraw = Transition(
        [RegistrationStateMachine.accepted],
        withdrawn,
        name=_('Withdraw'),
        description=_("Withdraw from this activity."),
        automatic=False,
        permission=is_user,
    )

    reapply = Transition(
        [withdrawn],
        RegistrationStateMachine.accepted,
        name=_('Reapply'),
        description=_("Reapply for this activity."),
        automatic=False,
        permission=is_user,
    )

    stop = Transition(
        [RegistrationStateMachine.accepted],
        stopped,
        name=_('Stop'),
        description=_("Stop contributing to this activity."),
        automatic=False,
        permission=RegistrationStateMachine.can_accept_registration,
    )

    start = Transition(
        [stopped],
        RegistrationStateMachine.accepted,
        name=_('Start again'),
        description=_("Start contributing to this activity again."),
        automatic=False,
        permission=RegistrationStateMachine.can_accept_registration,
    )
