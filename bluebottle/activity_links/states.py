from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.state import (
    EmptyState,
    ModelStateMachine,
    State,
    Transition,
    register,
)
from bluebottle.activity_links.models import LinkedActivity


@register(LinkedActivity)
class LinkedActivityStateMachine(ModelStateMachine):
    model = LinkedActivity

    open = State(
        _("Open"),
        "open",
        _("Open linked activities are shown in the open activities overview."),
    )

    succeeded = State(
        _("Succeeded"),
        "succeeded",
        _("Succeeded linked activities are shown in the succeeded activities overview."),
    )

    cancelled = State(
        _("Cancelled"),
        "cancelled",
        _("Cancelled linked activities are never shown."),
    )

    initiate = Transition(
        EmptyState(),
        open,
        name=_("Initiative"),
        description=_("The link will be created."),
    )

    succeed = Transition(
        [open],
        succeeded,
        name=_("Succeeded"),
        description=_("The initiative will be isucceeded."),
        automatic=True,
    )

    cancel = Transition(
        [open, succeeded],
        cancelled,
        name=_("Cancel"),
        description=_("The initiative will be cancelled."),
        automatic=True,
    )
