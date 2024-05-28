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


@register(TeamMember)
class TeamMemberStateMachine(ModelStateMachine):
    new = State(_("Unscheduled"), "new", _("This team member is unscheduled."))

    accepted = State(
        _("accepted"), "accepted", _("This team member has been accepted.")
    )

    rejected = State(
        _("rejected"), "rejected", _("This team member has been accepted.")
    )

    removed = State(_("removed"), "removed", _("This team member is removed."))

    initiate = Transition(
        EmptyState(),
        new,
        name=_("Initiate"),
        description=_("The team member joined."),
        automatic=True,
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

    remove = Transition(
        [accepted],
        removed,
        name=_("Removed"),
        description=_("Remove this team from the activity."),
        automatic=True,
    )

    readd = Transition(
        removed,
        accepted,
        name=_("Re-add"),
        description=_("Re-add team to activity."),
        automatic=True,
    )
