from bluebottle.activities.effects import (
    CreateOrganizer, CopyCategories, SetPublishedDateEffect,
    DeleteRelatedContributionsEffect, CreateOrganizerContribution,
    SetContributionDateEffect
)
from bluebottle.activities.messages.activity_manager import (
    ActivityPublishedNotification, ActivitySubmittedNotification,
    ActivityApprovedNotification, ActivityNeedsWorkNotification, TermsOfServiceNotification,
    ActivityCancelledNotification
)
from bluebottle.activities.messages.reviewer import (
    ActivitySubmittedReviewerNotification,
    ActivityPublishedReviewerNotification
)
from bluebottle.activities.models import Organizer, EffortContribution
from bluebottle.activities.states import (
    ActivityStateMachine, OrganizerStateMachine,
    EffortContributionStateMachine, ContributorStateMachine
)
from bluebottle.activity_pub.effects import (
    AnnounceAdoptionEffect, CreateEffect, UpdateEventEffect,
    CancelEffect, DeletedEffect
)
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    TriggerManager, TransitionTrigger, ModelDeletedTrigger, register, ModelChangedTrigger
)
from bluebottle.funding.models import Funding
from bluebottle.impact.effects import UpdateImpactGoalEffect
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.states import ParticipantStateMachine, SlotStateMachine, DateActivitySlotStateMachine


def should_approve_instantly(effect):
    if isinstance(effect.instance, Funding):
        return False
    review = InitiativePlatformSettings.load().enable_reviewing
    if effect.instance.initiative is None:
        return not review
    return effect.instance.initiative.status == 'approved'


def should_review(effect):
    if isinstance(effect.instance, Funding):
        return True
    review = InitiativePlatformSettings.load().enable_reviewing
    if effect.instance.initiative is None:
        return review
    return effect.instance.initiative.status != 'approved'


def has_organizer(effect):
    """
    Has an organizer
    """
    return getattr(effect.instance, 'organizer', False)


def is_not_funding(effect):
    """
    Is not a funding activity
    """
    return not isinstance(effect.instance, Funding)


def should_mail_tos(effect):
    """
    Should mail the terms of service
    """
    settings = InitiativePlatformSettings.load()
    return settings.mail_terms_of_service


class ActivityTriggers(TriggerManager):
    triggers = [
        ModelDeletedTrigger(
            effects=[DeletedEffect]
        ),
        TransitionTrigger(
            ActivityStateMachine.initiate,
            effects=[
                CreateOrganizer,
                CopyCategories
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.submit,
            effects=[
                TransitionEffect(
                    ActivityStateMachine.auto_approve,
                    conditions=[should_approve_instantly]
                ),
                NotificationEffect(
                    ActivitySubmittedReviewerNotification,
                    conditions=[should_review]
                ),
                NotificationEffect(
                    ActivitySubmittedNotification,
                    conditions=[
                        should_review,
                        is_not_funding
                    ]
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
            ActivityStateMachine.approve,
            effects=[
                CreateEffect,
                AnnounceAdoptionEffect,
                NotificationEffect(
                    ActivityApprovedNotification,
                    conditions=[is_not_funding]
                ),
                NotificationEffect(
                    TermsOfServiceNotification,
                    conditions=[should_mail_tos]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.request_changes,
            effects=[
                NotificationEffect(
                    ActivityNeedsWorkNotification,
                    conditions=[is_not_funding]
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
                ),
                CancelEffect,
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
            ActivityStateMachine.publish,
            effects=[
                SetPublishedDateEffect,
                AnnounceAdoptionEffect,
                CreateEffect,
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.succeed,
                    conditions=[has_organizer]
                ),
                NotificationEffect(ActivityPublishedReviewerNotification),
                NotificationEffect(ActivityPublishedNotification)
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]
                ),
                CancelEffect
            ]
        ),
        TransitionTrigger(
            ActivityStateMachine.auto_cancel,
            effects=[
                NotificationEffect(ActivityCancelledNotification),
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]
                ),
                RelatedTransitionEffect(
                    'contributors',
                    ContributorStateMachine.fail
                ),
                RelatedTransitionEffect(
                    'slots',
                    SlotStateMachine.auto_cancel
                ),
                RelatedTransitionEffect(
                    'slots',
                    DateActivitySlotStateMachine.auto_cancel
                ),
                CancelEffect
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.expire,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.fail,
                    conditions=[has_organizer]
                ),
                CancelEffect
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
                ),
                CancelEffect
            ]
        ),
        ModelChangedTrigger(
            ['title', 'description', 'status'],
            effects=[
                UpdateEventEffect,
            ]
        )
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
                    'contributions', EffortContributionStateMachine.reset, display=True
                )
            ]
        ),
        TransitionTrigger(
            OrganizerStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'contributions', EffortContributionStateMachine.succeed, display=True
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
