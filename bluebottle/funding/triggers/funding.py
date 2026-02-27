from django.utils import timezone

from bluebottle.activities.states import ContributorStateMachine
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import ActivityTriggers, ContributionTriggers
from bluebottle.activities.triggers import ContributorTriggers
from bluebottle.activity_pub.effects import (
    PublishAdoptionEffect, CreateEffect, UpdateEventEffect, CancelEffect, FinishEffect
)
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    ModelDeletedTrigger, ModelChangedTrigger, TransitionTrigger, register, TriggerManager
)
from bluebottle.funding.effects import (
    GeneratePayoutsEffect, GenerateDonorWallpostEffect,
    RemoveDonorWallpostEffect, UpdateFundingAmountsEffect, RefundPaymentAtPSPEffect, SetDeadlineEffect,
    DeletePayoutsEffect,
    SetDateEffect, RemoveDonorFromPayoutEffect, CreateDonationEffect,
    UpdateDonationValueEffect,
    RemoveAnonymousRewardEffect
)
from bluebottle.funding.messages.funding.activity_manager import (
    DonationSuccessActivityManagerMessage,
    FundingPartiallyFundedMessage, FundingExpiredMessage, FundingRealisedOwnerMessage,
    FundingRejectedMessage, FundingRefundedMessage, FundingExtendedMessage,
    FundingCancelledMessage, FundingApprovedMessage
)
from bluebottle.funding.messages.funding.activity_manager import FundingSubmittedMessage, FundingNeedsWorkMessage
from bluebottle.funding.messages.funding.contributor import (
    DonationSuccessDonorMessage,
    DonationRefundedDonorMessage,
    DonationActivityRefundedDonorMessage,
)
from bluebottle.funding.messages.funding.reviewer import FundingSubmittedReviewerMessage
from bluebottle.funding.models import (
    Funding, Donor, Payment, MoneyContribution, FundingPlatformSettings, )
from bluebottle.funding.states import (
    FundingStateMachine, DonorStateMachine, BasePaymentStateMachine,
    DonationStateMachine,
)
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.notifications.effects import NotificationEffect


def should_finish(effect):
    """the deadline has passed"""
    return effect.instance.deadline and effect.instance.deadline < timezone.now()


def without_approved_payouts(effect):
    """hasn't got approved payouts"""
    return not effect.instance.payouts.exclude(status__in=['new', 'failed']).count()


def is_complete(effect):
    """all required information has been submitted"""
    return not list(effect.instance.required)


def is_valid(effect):
    """all fields passed validation and are correct"""
    return not list(effect.instance.errors)


def deadline_in_future(effect):
    """the deadline is in the future"""
    if effect.instance.deadline:
        return effect.instance.deadline > timezone.now()
    return bool(effect.instance.duration)


def target_reached(effect):
    """target amount has been reached (100% or more)"""
    if not effect.instance.target:
        return False
    return effect.instance.amount_raised >= effect.instance.target


def target_not_reached(effect):
    """target amount has not been reached (less then 100%, but more then 0)"""
    return effect.instance.amount_raised.amount and effect.instance.amount_raised < effect.instance.target


def no_donations(effect):
    """no (successful) donations have been made"""
    return not effect.instance.donations.filter(status='succeeded').count()


def should_review(effect):
    if isinstance(effect.instance, Funding):
        return True
    review = InitiativePlatformSettings.load().enable_reviewing
    if effect.instance.initiative is None:
        return review
    return effect.instance.initiative.status != 'approved'


def fixed_target(effect):
    platform_settings = FundingPlatformSettings.load()
    return platform_settings.fixed_target


def campaign_target_reached(effect):
    """ the campaign target amount has been reached (100% or more)"""
    activity = effect.instance.activity
    if not activity.target:
        return False
    return activity.amount_raised >= activity.target


@register(Funding)
class FundingTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [

        TransitionTrigger(
            FundingStateMachine.submit,
            effects=[
                NotificationEffect(
                    FundingSubmittedReviewerMessage,
                    conditions=[should_review]
                ),
                NotificationEffect(
                    FundingSubmittedMessage,
                    conditions=[should_review]
                )
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.approve,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed),
                SetDateEffect('started'),
                SetDeadlineEffect,
                TransitionEffect(
                    FundingStateMachine.expire,
                    conditions=[should_finish]
                ),
                NotificationEffect(FundingApprovedMessage),
                CreateEffect,
                PublishAdoptionEffect
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(FundingCancelledMessage),
                CancelEffect,
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.reject,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(FundingRejectedMessage),
                CancelEffect
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.request_changes,
            effects=[
                NotificationEffect(FundingNeedsWorkMessage)
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.expire,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(FundingExpiredMessage),
                CancelEffect
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.extend,
            effects=[
                DeletePayoutsEffect,
                NotificationEffect(FundingExtendedMessage)
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.succeed,
            effects=[
                GeneratePayoutsEffect,
                NotificationEffect(FundingRealisedOwnerMessage),
                FinishEffect
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.recalculate,
            effects=[
                GeneratePayoutsEffect,
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.partial,
            effects=[
                GeneratePayoutsEffect,
                NotificationEffect(FundingPartiallyFundedMessage),
                FinishEffect
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.refund,
            effects=[
                RelatedTransitionEffect('donations', DonorStateMachine.activity_refund),
                DeletePayoutsEffect,
                NotificationEffect(FundingRefundedMessage)
            ]
        ),

        ModelChangedTrigger(
            'deadline',
            effects=[
                TransitionEffect(
                    FundingStateMachine.extend,
                    conditions=[
                        is_complete,
                        is_valid,
                        deadline_in_future,
                        without_approved_payouts
                    ]
                ),
                TransitionEffect(
                    FundingStateMachine.succeed,
                    conditions=[
                        should_finish,
                        target_reached
                    ]
                ),
                TransitionEffect(
                    FundingStateMachine.partial,
                    conditions=[
                        should_finish,
                        target_not_reached
                    ]
                ),
                TransitionEffect(
                    FundingStateMachine.cancel,
                    conditions=[
                        should_finish,
                        no_donations
                    ]
                ),
            ]
        ),

        ModelChangedTrigger(
            'target',
            effects=[
                TransitionEffect(
                    FundingStateMachine.succeed,
                    conditions=[should_finish, target_reached]
                ),
                TransitionEffect(
                    FundingStateMachine.partial,
                    conditions=[should_finish, target_not_reached]
                ),
                TransitionEffect(
                    FundingStateMachine.cancel,
                    conditions=[should_finish, no_donations]
                ),
            ]
        ),

        ModelChangedTrigger(
            'amount_matching',
            effects=[
                TransitionEffect(
                    FundingStateMachine.succeed,
                    conditions=[should_finish, target_reached]
                ),
                TransitionEffect(
                    FundingStateMachine.succeed,
                    conditions=[fixed_target, target_reached]
                ),
                TransitionEffect(
                    FundingStateMachine.partial,
                    conditions=[should_finish, target_not_reached]
                ),
            ]
        ),
        ModelChangedTrigger(
            'amount_donated',
            effects=[
                TransitionEffect(
                    FundingStateMachine.succeed,
                    conditions=[fixed_target, target_reached]
                ),
            ]
        ),
        ModelChangedTrigger(
            [
                'target', 'amount_donated', 'amount_matching', 'amount_pledged',
                'deadline', 'impact_location'
            ],
            effects=[
                UpdateEventEffect,
            ]
        )
    ]


def is_successful(effect):
    """donation is successful"""
    return effect.instance.status == ContributorStateMachine.succeeded


@register(Donor)
class DonorTriggers(ContributorTriggers):
    triggers = [
        TransitionTrigger(
            DonorStateMachine.initiate,
            effects=[
                CreateDonationEffect
            ]
        ),

        TransitionTrigger(
            DonorStateMachine.succeed,
            effects=[
                RelatedTransitionEffect('contributions', DonationStateMachine.succeed),
                NotificationEffect(DonationSuccessActivityManagerMessage),
                NotificationEffect(DonationSuccessDonorMessage),
                GenerateDonorWallpostEffect,
                FollowActivityEffect,
                UpdateFundingAmountsEffect,
                RemoveAnonymousRewardEffect,
            ]
        ),

        TransitionTrigger(
            DonorStateMachine.fail,
            effects=[
                RelatedTransitionEffect('contributions', DonationStateMachine.fail),
                RemoveDonorWallpostEffect,
                UpdateFundingAmountsEffect,
                RemoveDonorFromPayoutEffect
            ]
        ),

        TransitionTrigger(
            DonorStateMachine.expire,
            effects=[
                RelatedTransitionEffect('contributions', DonationStateMachine.fail),
            ]
        ),

        TransitionTrigger(
            DonorStateMachine.refund,
            effects=[
                RelatedTransitionEffect('contributions', DonationStateMachine.fail),
                RemoveDonorWallpostEffect,
                UnFollowActivityEffect,
                UpdateFundingAmountsEffect,
                RemoveDonorFromPayoutEffect,
                RelatedTransitionEffect('payment', BasePaymentStateMachine.request_refund),
                NotificationEffect(DonationRefundedDonorMessage)
            ]
        ),

        TransitionTrigger(
            DonorStateMachine.activity_refund,
            effects=[
                RelatedTransitionEffect('contributions', DonationStateMachine.fail),
                RelatedTransitionEffect('payment', BasePaymentStateMachine.request_refund),
                NotificationEffect(DonationActivityRefundedDonorMessage)
            ]
        ),

        ModelChangedTrigger(
            'payout_amount',
            effects=[
                UpdateFundingAmountsEffect,
                UpdateDonationValueEffect
            ]
        ),

        ModelDeletedTrigger(
            effects=[
                UpdateFundingAmountsEffect,
            ]
        )

    ]


@register(MoneyContribution)
class MoneyContributionTriggers(ContributionTriggers):
    pass


def donation_not_refunded(effect):
    """
    donation doesn't have status refunded or activity refunded
    """
    donation = effect.instance.donation
    return donation.status not in [
        DonorStateMachine.refunded.value,
        DonorStateMachine.activity_refunded.value,
    ]


@register(Payment)
class BasePaymentTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            BasePaymentStateMachine.authorize,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            BasePaymentStateMachine.succeed,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            BasePaymentStateMachine.require_action,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.set_pending)
            ]
        ),

        TransitionTrigger(
            BasePaymentStateMachine.fail,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            BasePaymentStateMachine.request_refund,
            effects=[
                RefundPaymentAtPSPEffect
            ]
        ),

        TransitionTrigger(
            BasePaymentStateMachine.refund,
            effects=[
                RelatedTransitionEffect(
                    'donation',
                    DonorStateMachine.refund,
                    conditions=[
                        donation_not_refunded
                    ]
                ),
            ]
        ),
    ]
