from bluebottle.activities.effects import (
    CreateOrganizer, CreateOrganizerContribution, SetContributionDateEffect, DeleteRelatedContributionsEffect,
    SetPublishedDateEffect, )
from bluebottle.activities.models import Organizer, EffortContribution
from bluebottle.activities.states import (
    ActivityStateMachine, OrganizerStateMachine,
    EffortContributionStateMachine
)
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    TriggerManager, TransitionTrigger, ModelDeletedTrigger, register
)
from bluebottle.funding.models import Funding
from bluebottle.impact.effects import UpdateImpactGoalEffect
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.time_based.states import ParticipantStateMachine


def should_approve_instantly(effect):
    if isinstance(effect.instance, Funding):
        return False
    review = InitiativePlatformSettings.load().enable_reviewing
    if effect.instance.initiative is None:
        return not review
    return effect.instance.initiative.status == 'approved'


def has_organizer(effect):
    """
    Has an organizer
    """
    return getattr(effect.instance, 'organizer', False)


class ActivityTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            ActivityStateMachine.initiate,
            effects=[
                CreateOrganizer
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.submit,
            effects=[
                TransitionEffect(
                    ActivityStateMachine.auto_approve,
                    conditions=[should_approve_instantly]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.auto_submit,
            effects=[
                TransitionEffect(
                    ActivityStateMachine.auto_approve,
                    conditions=[should_approve_instantly]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.auto_approve,
            effects=[
                SetPublishedDateEffect,
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.succeed,
                    conditions=[has_organizer]
                ),
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.expire,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]),
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.restore,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.reset,
                    conditions=[has_organizer]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.delete,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]
                )
            ]
        ),
    ]


class ContributorTriggers(TriggerManager):
    triggers = [
        ModelDeletedTrigger(
            effects=[
                DeleteRelatedContributionsEffect
            ]
        )
    ]


class ContributionTriggers(TriggerManager):
    triggers = []


@register(Organizer)
class OrganizerTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            OrganizerStateMachine.initiate,
            effects=[
                CreateOrganizerContribution
            ]
        ),
        TransitionTrigger(
            OrganizerStateMachine.fail,
            effects=[
                RelatedTransitionEffect(
                    'contributions', EffortContributionStateMachine.fail, display=False
                )
            ]
        ),
        TransitionTrigger(
            OrganizerStateMachine.reset,
            effects=[
                RelatedTransitionEffect(
                    'contributions', EffortContributionStateMachine.reset, display=False
                )
            ]
        ),
        TransitionTrigger(
            OrganizerStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'contributions', EffortContributionStateMachine.succeed, display=False
                )
            ]
        ),
    ]


def contributor_is_succeeded(effect):
    return effect.instance.contributor.status == 'succeeded'


@register(EffortContribution)
class EffortContributionTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            EffortContributionStateMachine.initiate,
            effects=[
                UpdateImpactGoalEffect,
                TransitionEffect(
                    EffortContributionStateMachine.succeed,
                    conditions=[contributor_is_succeeded]
                )
            ]
        ),
        TransitionTrigger(
            EffortContributionStateMachine.succeed,
            effects=[
                SetContributionDateEffect,
                UpdateImpactGoalEffect
            ]
        ),

        TransitionTrigger(
            EffortContributionStateMachine.reset,
            effects=[
                UpdateImpactGoalEffect
            ]
        ),

        TransitionTrigger(
            EffortContributionStateMachine.fail,
            effects=[
                UpdateImpactGoalEffect
            ]
        ),

        ModelDeletedTrigger(
            effects=[
                UpdateImpactGoalEffect
            ]
        ),
    ]


def activity_is_active(contribution):
    """activity is not cancelled, expired or rejected"""
    return contribution.contributor.activity.status not in [
        ActivityStateMachine.cancelled.value,
        ActivityStateMachine.expired.value,
        ActivityStateMachine.rejected.value
    ]


def contributor_is_active(contribution):
    """contributor is accepted"""
    return contribution.contributor.status in [
        ParticipantStateMachine.accepted.value
    ]


def needs_review(effect):
    """
    needs review
    """
    return hasattr(effect.instance.activity, 'review') and effect.instance.activity.review
