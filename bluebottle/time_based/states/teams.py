from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import register, ModelStateMachine, Transition, EmptyState, State
from bluebottle.time_based.models import TeamMember, Team


@register(Team)
class TeamStateMachine(ModelStateMachine):
    new = State(_("Pending"), "new", _("This team is pending review."))
    accepted = State(_("Unscheduled"), "accepted", _("This team has been accepted."))
    rejected = State(_("Rejected"), "rejected", _("This team has been rejected."))
    withdrawn = State(_("Withdrawn"), "withdrawn", _("This team has withdrawn."))

    scheduled = State(_("Scheduled"), "scheduled", _("This team has been scheduled."))
    succeeded = State(_("Succeeded"), "succeeded", _("This team was successful."))

    cancelled = State(_("Cancelled"), "cancelled", _("This team has been cancelled."))
    removed = State(
        _("Removed"), "removed", _("This team is removed from the activity")
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
        passed_label=_("accepted"),
        description=_("Accept this team."),
        automatic=True,
    )

    reject = Transition(
        [new, accepted],
        rejected,
        name=_("Reject"),
        passed_label=_("rejected"),
        description=_("Reject this team."),
        automatic=True,
    )

    schedule = Transition(
        [new, accepted],
        scheduled,
        name=_("Schedule"),
        passed_label=_("scheduled"),
        description=_("Assign a slot to this activity"),
        automatic=True,
    )

    remove = Transition(
        [accepted, scheduled],
        removed,
        name=_("Remove"),
        passed_label=_("removed"),
        description=_("Remove this team from the activity."),
        automatic=False,
        permission=is_manager,
    )

    readd = Transition(
        removed,
        accepted,
        name=_("Re-add"),
        passed_label=_("re-added"),
        description=_("Re-add team to activity."),
        automatic=False,
        permission=is_manager,
    )

    withdraw = Transition(
        [scheduled],
        withdrawn,
        name=_("Withdraw"),
        passed_label=_("withdrawn"),
        automatic=False,
        permission=is_owner,
        hide_from_admin=True,
        description=_(
            "Your team will no longer participate in this activity. "
            "The activity manager and team members will be notified. Any hours spent will not be be counted."
        ),
        short_description=_("Your team will no longer participate in this activity. "),
    )

    rejoin = Transition(
        withdrawn,
        accepted,
        name=_("Rejoin"),
        passed_label=_("rejoined"),
        automatic=False,
        permission=is_owner,
        hide_from_admin=True,
        description=_(
            'Join again with your team, that was previously withdrawn.'
        ),
    )

    cancel = Transition(
        [new, accepted, scheduled, succeeded],
        cancelled,
        name=_("Cancel"),
        passed_label=_("cancelled"),
        automatic=True,
        description=_(
            'This team will no longer participate in this activity and any hours spent will not be counted.'
        ),
    )

    restore = Transition(
        cancelled,
        new,
        name=_('Restore'),
        automatic=True,
        passed_label=_("restored"),
        description=_("Add this previously cancelled team back to the activity."),
    )

    succeed = Transition(
        [cancelled, scheduled, new, accepted],
        succeeded,
        name=_('Succeed'),
        automatic=True,
        description=_(
            'The team has finished their contribution.'
        ),
    )


@register(TeamMember)
class TeamMemberStateMachine(ModelStateMachine):
    active = State(_("Active"), "active", _("This team member is active."))
    removed = State(_("Removed"), "removed", _("This team member is removed."))
    withdrawn = State(_("Withdrawn"), "withdrawn", _("This team member is withdrawn."))
    cancelled = State(_("Cancelled"), "cancelled", _("This team member is cancelled."))
    rejected = State(_("Rejected"), "rejected", _("This team member is rejected."))

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
        passed_label=_("removed"),
        description=_("Remove this member from the team."),
    )

    auto_remove = Transition(
        [active],
        removed,
        automatic=True,
        name=_("Auto remove"),
        passed_label=_("removed"),
        description=_("Remove this member because the team has been removed."),
    )

    readd = Transition(
        [
            removed,
            cancelled
        ],
        active,
        automatic=False,
        permission=is_manager,
        name=_("Re-add"),
        passed_label=_("re-added"),
        description=_("Re-add member to team."),
    )

    withdraw = Transition(
        [active],
        withdrawn,
        name=_("Withdraw"),
        passed_label=_("withdrawn"),
        hide_from_admin=True,
        permission=is_owner,
        description=_("Withdraw from this team."),
        automatic=False,
    )

    reapply = Transition(
        withdrawn,
        active,
        name=_("Re-apply"),
        passed_label=_("re-applied"),
        hide_from_admin=True,
        permission=is_owner,
        description=_("Re-apply to team."),
        automatic=False,
    )

    reject = Transition(
        [active],
        rejected,
        name=_("Rejected"),
        passed_label=_("rejected"),
        description=_("Reject user from this team."),
        automatic=True,
    )
    accept = Transition(
        rejected,
        active,
        name=_("accept"),
        passed_label=_("accepted"),
        description=_("Accept user to team."),
        automatic=True,
    )

    cancel = Transition(
        [active],
        cancelled,
        name=_("Cancel"),
        passed_label=_("cancelled"),
        automatic=True,
        description=_("Cancel this team member, because the team is cancelled."),
    )

    restore = Transition(
        [cancelled],
        active,
        name=_("Restore"),
        passed_label=_("restored"),
        automatic=True,
        description=_("Restore this team member, because the team is restored."),
    )
