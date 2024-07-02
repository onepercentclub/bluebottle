from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import (
    register, State, Transition, EmptyState, ModelStateMachine
)
from bluebottle.time_based.models import (
    DeadlineRegistration,
    PeriodicRegistration, ScheduleRegistration, TeamScheduleRegistration, )


class RegistrationStateMachine(ModelStateMachine):
    new = State(
        _('Pending'),
        'new',
        _("This person has applied and must be reviewed.")
    )
    accepted = State(
        _('Accepted'),
        'accepted',
        _('This person is accepted to take part in the activity.')
    )
    rejected = State(
        _('Rejected'),
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

    add = Transition(
        new,
        accepted,
        name=_('Add'),
        description=_("Automatically add this person as a participant to the activity."),
        passed_label=_('added'),
        automatic=True,
    )

    accept = Transition(
        [new, rejected],
        accepted,
        name=_('Accept'),
        description=_("Accept this person as a participant of this activity."),
        passed_label=_('accepted'),
        automatic=False,
        permission=can_accept_registration,
    )

    reject = Transition(
        [new, accepted],
        rejected,
        name=_('Reject'),
        description=_("Reject this person as a participant of this activity."),
        automatic=False,
        permission=can_accept_registration,
    )


@register(DeadlineRegistration)
class DeadlineRegistrationStateMachine(RegistrationStateMachine):
    pass


@register(ScheduleRegistration)
class ScheduleRegistrationStateMachine(RegistrationStateMachine):
    def is_user(self, user):
        """is the participant"""
        return user == self.instance.user

    withdrawn = State(
        _('Withdrawn'),
        'withdrawn',
        _("This person has withdrawn from the activity. Contributions are not counted.")
    )

    withdraw = Transition(
        [RegistrationStateMachine.accepted, RegistrationStateMachine.new],
        withdrawn,
        name=_('Withdraw'),
        description=_("Withdraw from this activity."),
        automatic=False,
        permission=is_user,
    )

    reapply = Transition(
        [withdrawn],
        RegistrationStateMachine.new,
        name=_('Reapply'),
        description=_("Reapply for this activity."),
        automatic=False,
        permission=is_user,
    )


@register(TeamScheduleRegistration)
class TeamScheduleRegistrationStateMachine(ScheduleRegistrationStateMachine):
    pass


@register(PeriodicRegistration)
class PeriodicRegistrationStateMachine(RegistrationStateMachine):

    def is_user(self, user):
        """is the participant"""
        return user == self.instance.user

    def is_user_or_manager(self, user):
        return self.is_user(user) or self.can_accept_registration(user)

    withdrawn = State(
        _('Withdrawn'),
        'withdrawn',
        _("This person has withdrawn from the activity. Contributions are not counted.")
    )

    stopped = State(
        _('Stopped'),
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
        description=_(
            "This person will no longer actively participate in your activity and "
            "their contribution hours will stop being counted. The hours that have "
            "already been counted will be retained. You can resume their participation "
            "anytime."
        ),
        short_description=_("This person will no longer actively participate."),
        automatic=False,
        permission=is_user_or_manager,
    )

    start = Transition(
        [stopped],
        RegistrationStateMachine.accepted,
        name=_("Resume"),
        description=_(
            "This person will start actively participating in the activity and their "
            "contribution hours will be counted. You can stop their participation at "
            "any time, and their contribution hours will stop being counted."
        ),
        short_description=_("Resume this persons participation in your activity."),
        automatic=False,
        permission=is_user_or_manager,
    )
