from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import register, ModelStateMachine, Transition, EmptyState, State
from bluebottle.time_based.models import TeamMember, Team


@register(Team)
class TeamStateMachine(ModelStateMachine):
    new = State(_("Unscheduled"), "new", _("This team is unscheduled."))
    accepted = State(_("Accepted"), "accepted", _("This team has been accepted."))
    rejected = State(_("Rejected"), "rejected", _("This team has been rejected."))
    withdrawn = State(_("Withdrawn"), "withdrawn", _("This team has withdrawn."))

    scheduled = State(
        _('Scheduled'),
        'scheduled',
        _("This team has been scheduled.")
    )

    cancelled = State(
        _('Cancelled'),
        'cancelled',
        _("This team has been cancelled.")
    )

    def is_manager(self, user):
        return (
            user in self.instance.activity.initiative.activity_managers.all()
            or user == self.instance.activity.owner
            or user == self.instance.activity.initiative.owner
            or user.is_staff
            or user.is_superuser
        )

    def is_owner(self, user):
        return user == self.instance.user

    initiate = Transition(
        EmptyState(),
        new,
        name=_('Initiate'),
        description=_(
            'The team was created.'
        ),
    )

    accept = Transition(
        [new, rejected],
        accepted,
        name=_("Accept"),
        description=_("Accept this team."),
        automatic=True,
    )

    reject = Transition(
        [new, accepted],
        rejected,
        name=_("Reject"),
        description=_("Reject this team."),
        automatic=True,
    )

    schedule = Transition(
        [new, accepted],
        scheduled,
        name=_("Schedule"),
        description=_("Assign a slot to this activity"),
        automatic=True,
    )

    cancel = Transition(
        [new, accepted, scheduled],
        cancelled,
        name=_('Cancel'),
        automatic=False,
        permission=is_manager,
        description=_(
            'This team will no longer participate in this activity and any hours spent will not be counted.'
        ),
    )

    restore = Transition(
        cancelled,
        accepted,
        name=_('Restore'),
        automatic=False,
        permission=is_manager,
        description=_(
            'Add this previously cancelled team back to the activity.'
        ),
    )

    withdraw = Transition(
        [new, accepted, scheduled],
        withdrawn,
        name=_('Withdrawn'),
        automatic=False,
        permission=is_owner,
        hide_from_admin=True,
        description=_(
            'Withdraw your team. You will no longer participate in '
            'this activity and any hours spent will not be counted.'
        ),
    )

    rejoin = Transition(
        withdrawn,
        accepted,
        name=_('Rejoin'),
        automatic=False,
        permission=is_owner,
        hide_from_admin=True,
        description=_(
            'Join again with your team, that was previously withdrawn.'
        ),
    )


@register(TeamMember)
class TeamMemberStateMachine(ModelStateMachine):
    active = State(_("Active"), "active", _("This team member is active."))
    removed = State(_("Removed"), "removed", _("This team member is removed."))
    withdrawn = State(_("Withdrawn"), "withdrawn", _("This team member is withdrawn."))
    cancelled = State(_("Cancelled"), "cancelled", _("This team member is cancelled."))

    def is_manager(self, user):
        return (
            user == self.instance.team.user
            or user in self.instance.team.activity.initiative.activity_managers.all()
            or user == self.instance.team.activity.owner
            or user == self.instance.team.activity.initiative.owner
            or user.is_staff
            or user.is_superuser
        )

    def is_owner(self, user):
        return user == self.instance.user

    initiate = Transition(
        EmptyState(),
        active,
        name=_("Initiate"),
        description=_("The team member joined."),
        automatic=True,
    )

    remove = Transition(
        [active],
        removed,
        automatic=False,
        permission=is_manager,
        name=_("Remove"),
        description=_("Remove this member from the team."),
    )

    readd = Transition(
        removed,
        active,
        automatic=False,
        permission=is_manager,
        name=_("Re-add"),
        description=_("Re-add member to team."),
    )

    withdraw = Transition(
        [active],
        withdrawn,
        name=_("Withdraw"),
        hide_from_admin=True,
        permission=is_owner,
        description=_("Withdraw from this team."),
    )

    reapply = Transition(
        withdrawn,
        active,
        name=_("Re-apply"),
        hide_from_admin=True,
        permission=is_owner,
        description=_("Re-apply to team."),
    )

    cancel = Transition(
        [active],
        cancelled,
        name=_("Cancel"),
        automatic=True,
        description=_("Cancel this team member, because the team is cancelled."),
    )

    restore = Transition(
        [cancelled],
        active,
        name=_("Restore"),
        automatic=True,
        description=_("Restore this team member, because the team is restored."),
    )
