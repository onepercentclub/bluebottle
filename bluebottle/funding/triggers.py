from django.utils import timezone
from decimal import Decimal

from bluebottle.activities.states import ContributorStateMachine
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import ActivityTriggers, ContributionTriggers
from bluebottle.activities.triggers import ContributorTriggers
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    ModelChangedTrigger, TransitionTrigger, register, TriggerManager
)
from bluebottle.funding.effects import (
    GeneratePayoutsEffect,
    UpdateFundingAmountsEffect, RefundPaymentAtPSPEffect, SetDeadlineEffect,
    DeletePayoutsEffect,
    SubmitPayoutEffect, SetDateEffect, DeleteDocumentEffect,
    ClearPayoutDatesEffect, RemoveDonorFromPayoutEffect, CreateDonationEffect, UpdateDonationValueEffect
)
from bluebottle.funding.messages import (
    DonationSuccessActivityManagerMessage, DonationSuccessDonorMessage,
    FundingPartiallyFundedMessage, FundingExpiredMessage, FundingRealisedOwnerMessage,
    PayoutAccountVerified, PayoutAccountRejected,
    DonationRefundedDonorMessage, DonationActivityRefundedDonorMessage,
    FundingRejectedMessage, FundingRefundedMessage, FundingExtendedMessage,
    FundingCancelledMessage, FundingApprovedMessage

)
from bluebottle.funding.models import Funding, PlainPayoutAccount, Donor, Payout, Payment, BankAccount, \
    MoneyContribution
from bluebottle.funding.states import (
    FundingStateMachine, DonorStateMachine, BasePaymentStateMachine,
    PayoutStateMachine, BankAccountStateMachine, PlainPayoutAccountStateMachine, DonationStateMachine
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.events.effects import TriggerEvent


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


def reached_percentage(effect, percentage):
    activity = effect.instance
    target = activity.target.amount / Decimal(100 / percentage)

    raised = activity.amount_raised.amount
    try:
        initial_donated = activity._initial_values['amount_donated'].amount
        initial_matching = activity._initial_values['amount_matching'].amount

        return raised >= target and (initial_donated + initial_matching) < target
    except AttributeError:
        return False


def reached_50_percent(effect):
    return reached_percentage(effect, 50)


def reached_100_percent(effect):
    return reached_percentage(effect, 100)


@register(Funding)
class FundingTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [

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
                TriggerEvent('funding.approved')
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(FundingCancelledMessage)
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.reject,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(FundingRejectedMessage)
            ]
        ),

        TransitionTrigger(
            FundingStateMachine.expire,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(FundingExpiredMessage),
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
                TriggerEvent('funding.succeeded')
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
                NotificationEffect(FundingPartiallyFundedMessage)
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
                    FundingStateMachine.partial,
                    conditions=[should_finish, target_not_reached]
                ),
            ]
        ),

        ModelChangedTrigger(
            'amount_raised',
            effects=[
                TriggerEvent('funding.50%', conditions=[reached_50_percent]),
                TriggerEvent('funding.100%', conditions=[reached_100_percent]),
            ]
        )
    ]


def is_reviewed(effect):
    """has been verified"""
    return effect.instance.reviewed


def is_unreviewed(effect):
    """has not been verified"""
    return not effect.instance.reviewed


@register(PlainPayoutAccount)
class PlainPayoutAccountTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            PlainPayoutAccountStateMachine.verify,
            effects=[
                NotificationEffect(PayoutAccountVerified),
                DeleteDocumentEffect
            ]
        ),

        TransitionTrigger(
            PlainPayoutAccountStateMachine.reject,
            effects=[
                NotificationEffect(PayoutAccountRejected),
                DeleteDocumentEffect
            ]
        ),
    ]


@register(BankAccount)
class BankAccountTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            BankAccountStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    'connect_account',
                    PlainPayoutAccountStateMachine.reject,
                    description='Reject connected KYC account'
                )
            ]
        ),
    ]


@register(Payout)
class PayoutTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            PayoutStateMachine.approve,
            effects=[
                SubmitPayoutEffect,
                SetDateEffect('date_approved')
            ]
        ),

        TransitionTrigger(
            PayoutStateMachine.start,
            effects=[
                SetDateEffect('date_started')
            ]
        ),

        TransitionTrigger(
            PayoutStateMachine.reset,
            effects=[
                ClearPayoutDatesEffect
            ]
        ),

        TransitionTrigger(
            PayoutStateMachine.schedule,
            effects=[
                ClearPayoutDatesEffect
            ]
        ),

        TransitionTrigger(
            PayoutStateMachine.succeed,
            effects=[
                SetDateEffect('date_completed')
            ]
        ),
    ]


def is_successful(instance):
    """donation is successful"""
    return instance.instance.status == ContributorStateMachine.succeeded


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
                FollowActivityEffect,
                UpdateFundingAmountsEffect,
                TriggerEvent('donation.succeeded')
            ]
        ),

        TransitionTrigger(
            DonorStateMachine.fail,
            effects=[
                RelatedTransitionEffect('contributions', DonationStateMachine.fail),
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
