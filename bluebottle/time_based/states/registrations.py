from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import (
    register, State, Transition, EmptyState, ModelStateMachine
)
from bluebottle.time_based.models import (
    DeadlineRegistration,
    PeriodicRegistration, ScheduleRegistration, TeamScheduleRegistration, DateRegistration, )


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

    withdrawn = State(
        _('Withdrawn'),
        'withdrawn',
        _("This person did not participate.")
    )

    def can_accept_registration(self, user):
        """can accept participant"""
        return (
            user in self.instance.activity.owners or
            user.is_superuser or
            user.is_staff
        )

    def is_user(self, user):
        """is participant"""
        return self.instance.user == user

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

    withdraw = Transition(
        [
            new,
            accepted,
        ],
        withdrawn,
        name=_("Withdraw"),
        passed_label=_("withdrawn"),
        description=_(
            "Cancel your participation in the activity. Participation hours will not be counted."
        ),
        automatic=False,
        permission=is_user,
        hide_from_admin=True,
    )

    restore = Transition(
        withdrawn,
        new,
        name=_("Restore"),
        passed_label=_("restored"),
        description=_(
            "Restore after being withdrawn."
        ),
        automatic=True,
        hide_from_admin=True,
    )


@register(DateRegistration)
class DateRegistrationStateMachine(RegistrationStateMachine):
    pass


@register(DeadlineRegistration)
class DeadlineRegistrationStateMachine(RegistrationStateMachine):
    pass


@register(ScheduleRegistration)
class ScheduleRegistrationStateMachine(RegistrationStateMachine):
    def is_user(self, user):
        """is the participant"""
        return user == self.instance.user


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

    stopped = State(
        _('Stopped'),
        'stopped',
        _("This person stopped contributing to this activity.")
    )

    removed = State(
        _('Removed'),
        'removed',
        _("This person was removed from this activity.")
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

    remove = Transition(
        [RegistrationStateMachine.accepted],
        removed,
        name=_('Remove'),
        description=_(
            "This person will no longer actively participate in your activity and "
            "their contribution hours will stop being counted. The hours that have "
            "already been counted will be failed."
        ),
        short_description=_("This person is removed from the activity."),
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
