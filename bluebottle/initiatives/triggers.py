from bluebottle.activities.states import ActivityStateMachine
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger, TriggerManager, register, ModelChangedTrigger
from bluebottle.initiatives.messages import (
    InitiativeRejectedOwnerMessage, InitiativeApprovedOwnerMessage,
    InitiativeCancelledOwnerMessage, AssignedReviewerMessage, InitiativeSubmittedStaffMessage
)
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.states import ReviewStateMachine
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.states import DateStateMachine, TimeBasedStateMachine


def reviewer_is_set(effect):
    return effect.instance.reviewer is not None


def has_status(effect, status):
    return effect.instance.status == status


def is_submitted(effect):
    return has_status(effect, "submitted")


def is_approved(effect):
    return has_status(effect, "approved")


def is_rejected(effect):
    return has_status(effect, "rejected")


def is_cancelled(effect):
    return has_status(effect, "cancelled")


def is_deleted(effect):
    return has_status(effect, "deleted")


def needs_work(effect):
    return has_status(effect, "needs_work")


@register(Initiative)
class InitiativeTriggers(TriggerManager):
    triggers = []
