from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import register, ModelStateMachine, Transition, EmptyState, State
from bluebottle.time_based.models import TeamMember, Team


@register(Team)
class TeamStateMachine(ModelStateMachine):
    new = State(_("Unscheduled"), "new", _("This team is unscheduled."))

    accepted = State(_("accepted"), "accepted", _("This team has been accepted."))

    rejected = State(_("rejected"), "rejected", _("This team has been accepted."))

    scheduled = State(_("Scheduled"), "scheduled", _("This team is scheduled"))

    removed = State(
        _("Removed"), "removed", _("This team is removed from the activity")
    )

    scheduled = State(
        _('scheduled'),
        'scheduled',
        _("This team has been scheduled.")
    )

    cancelled = State(
        _('cancelled'),
        'cancelled',
        _("This team has been cancelled.")
    )

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

    remove = Transition(
        [accepted, scheduled],
        removed,
        name=_("Remove"),
        description=_("Remove this team from the activity."),
        automatic=False,
    )

    readd = Transition(
        removed,
        accepted,
        name=_("Re-add"),
        description=_("Re-add team to activity."),
        automatic=False,
    )
    cancel = Transition(
        [new, accepted, scheduled],
        cancelled,
        name=_('Cancel'),
        automatic=False,
        description=_(
            'The team has been cancelled.'
        ),
    )

    restore = Transition(
        cancelled,
        new,
        name=_('Restore'),
        automatic=False,
        description=_(
            'The team has been restored.'
        ),
    )


@register(TeamMember)
class TeamMemberStateMachine(ModelStateMachine):
    active = State(_("Active"), "active", _("This team member is active."))
    removed = State(_("removed"), "removed", _("This team member is removed."))
    withdrawn = State(_("withdrawn"), "withdrawn", _("This team member is withdrawn."))

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
        name=_("Remove"),
        description=_("Remove this member from the team."),
        automatic=False,
    )
    readd = Transition(
        removed,
        active,
        name=_("Re-add"),
        description=_("Re-add member to team."),
        automatic=False,
    )

    withdraw = Transition(
        [active],
        withdrawn,
        name=_("Withdraw"),
        description=_("Withdraw from this team."),
        automatic=False,
    )
    reapply = Transition(
        withdrawn,
        active,
        name=_("Re-apply"),
        description=_("Re-apply to team."),
        automatic=False,
    )
