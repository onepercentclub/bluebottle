from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import (
    TransitionEffect,
    RelatedTransitionEffect
)
from bluebottle.fsm.state import Transition, ModelStateMachine, State
from bluebottle.funding.effects import GeneratePayouts, GenerateDonationWallpost, \
    RemoveDonationWallpost, UpdateFundingAmounts, RefundPaymentAtPSP, SetStartDate, SetDeadline, DeletePayouts
from bluebottle.funding.messages import DonationSuccessActivityManagerMessage, DonationSuccessDonorMessage, \
    FundingPartiallyFundedMessage, FundingClosedMessage, FundingRealisedOwnerMessage, PayoutAccountVerified
from bluebottle.funding.models import Funding, Donation, Payout, Payment, PayoutAccount
from bluebottle.notifications.effects import NotificationEffect


class FundingStateMachine(ActivityStateMachine):

    model = Funding

    partially_funded = State(_('partially funded'), 'partially_funded')
    refunded = State(_('refunded'), 'refunded')

    def should_finish(self):
        """the deadline has passed"""
        return self.instance.deadline and self.instance.deadline < timezone.now()

    def deadline_in_future(self):
        return self.instance.deadline > timezone.now()

    def target_reached(self):
        return self.instance.amount_raised >= self.instance.target

    def target_not_reached(self):
        return self.instance.amount_raised.amount and self.instance.amount_raised < self.instance.target

    def no_donations(self):
        return not self.instance.amount_raised.amount

    def without_approved_payouts(self):
        return not self.instance.payouts.exclude(status__in=['new', 'failed']).count()

    def can_approve(self, user):
        return user.is_staff

    submit = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work
        ],
        ActivityStateMachine.submitted,
        name=_('Submit'),
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid
        ],
        automatic=False
    )

    approve = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
            ActivityStateMachine.submitted,
            ActivityStateMachine.rejected
        ],
        ActivityStateMachine.open,
        name=_('Approve'),
        automatic=False,
        permission=can_approve,
        effects=[
            RelatedTransitionEffect('organizer', 'succeed'),
            SetStartDate,
            SetDeadline,
            TransitionEffect(
                'close',
                conditions=[should_finish]
            ),
        ]
    )

    close = Transition(
        [ActivityStateMachine.open],
        ActivityStateMachine.closed,
        name=_('Close'),
        automatic=True,
        effects=[
            NotificationEffect(FundingClosedMessage)
        ]
    )

    extend = Transition(
        [
            ActivityStateMachine.succeeded,
            partially_funded,
            ActivityStateMachine.closed,
        ],
        ActivityStateMachine.open,
        name=_('Extend'),
        automatic=True,
        effects=[
            DeletePayouts
        ]
    )

    succeed = Transition(
        [ActivityStateMachine.open, partially_funded],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
        effects=[
            GeneratePayouts,
            NotificationEffect(FundingRealisedOwnerMessage)
        ]
    )

    recalculate = Transition(
        [
            ActivityStateMachine.succeeded,
            partially_funded
        ],
        ActivityStateMachine.succeeded,
        name=_('Recalculate'),
        automatic=False,
        conditions=[
            target_reached
        ],
        effects=[
            GeneratePayouts
        ]
    )

    partial = Transition(
        [ActivityStateMachine.open, ActivityStateMachine.succeeded, ActivityStateMachine.closed],
        partially_funded,
        name=_('Partial'),
        automatic=True,
        effects=[
            GeneratePayouts,
            NotificationEffect(FundingPartiallyFundedMessage)
        ]
    )

    refund = Transition(
        [ActivityStateMachine.succeeded, partially_funded],
        refunded,
        name=_('Refund'),
        automatic=False,
        effects=[
            RelatedTransitionEffect('donations', 'activity_refund'),
            DeletePayouts
        ]
    )


class DonationStateMachine(ContributionStateMachine):
    model = Donation
    failed = State(_('failed'), 'failed')
    refunded = State(_('refunded'), 'refunded')
    activity_refunded = State(_('activity_refunded'), 'activity_refunded')

    succeed = Transition(
        [
            ContributionStateMachine.new,
            ContributionStateMachine.failed
        ],
        ContributionStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
        effects=[
            NotificationEffect(DonationSuccessActivityManagerMessage),
            NotificationEffect(DonationSuccessDonorMessage),
            GenerateDonationWallpost,
            FollowActivityEffect,
            UpdateFundingAmounts
        ]
    )

    fail = Transition(
        [
            ContributionStateMachine.new,
            ContributionStateMachine.succeeded
        ],
        failed,
        name=_('Fail'),
        automatic=True,
        effects=[
            RemoveDonationWallpost,
            UpdateFundingAmounts
        ]
    )

    refund = Transition(
        [
            ContributionStateMachine.new,
            ContributionStateMachine.succeeded
        ],
        refunded,
        name=_('Refund'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('payment', 'request_refund'),
            RemoveDonationWallpost,
            UnFollowActivityEffect,
            UpdateFundingAmounts
        ]
    )

    activity_refund = Transition(
        [
            ContributionStateMachine.new,
            ContributionStateMachine.succeeded,
        ],
        activity_refunded,
        name=_('Activity refund'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('payment', 'request_refund'),
            RemoveDonationWallpost
        ]
    )


class PaymentStateMachine(ModelStateMachine):
    model = Payment

    new = State(_('new'), 'new')
    pending = State(_('pending'), 'pending')
    succeeded = State(_('succeeded'), 'succeeded')
    failed = State(_('failed'), 'failed')
    refunded = State(_('refunded'), 'refunded')
    refund_requested = State(_('refund requested'), 'refund_requested')

    authorize = Transition(
        [new],
        pending,
        name=_('Authorize'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'succeed')
        ]
    )

    succeed = Transition(
        [new, pending, failed],
        succeeded,
        name=_('Succeed'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'succeed')
        ]
    )

    fail = Transition(
        [new, pending, succeeded],
        failed,
        name=_('Fail'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'fail')
        ]
    )

    request_refund = Transition(
        [
            ContributionStateMachine.succeeded
        ],
        refund_requested,
        name=_('Request refund'),
        automatic=True,
        effects=[
            RefundPaymentAtPSP
        ]
    )

    refund = Transition(
        [
            ContributionStateMachine.succeeded
        ],
        refunded,
        name=_('Refund'),
        automatic=True
    )


class PayoutStateMachine(ModelStateMachine):
    model = Payout

    new = State(_('new'), 'new')
    approved = State(_('approve'), 'approve')
    scheduled = State(_('scheduled'), 'scheduled')
    started = State(_('started'), 'started')
    succeeded = State(_('succeeded'), 'succeeded')
    failed = State(_('failed'), 'failed')

    approve = Transition(
        new,
        approved,
        name=_('Approve'),
        automatic=False
    )

    start = Transition(
        new,
        started,
        name=_('Start'),
        automatic=True
    )

    reset = Transition(
        [approved, scheduled, started, succeeded, failed],
        new,
        name=_('Reset'),
        automatic=True
    )

    succeed = Transition(
        [approved, scheduled, started, failed],
        succeeded,
        name=_('Succeed'),
        automatic=True
    )

    cancel = Transition(
        [new, approved],
        failed,
        name=_('Cancel'),
        automatic=True
    )


class PayoutAccountStateMachine(ModelStateMachine):
    model = PayoutAccount

    new = State(_('new'), 'new')
    pending = State(_('pending'), 'pending')
    verified = State(_('verified'), 'verified')
    rejected = State(_('rejected'), 'rejected')
    incomplete = State(_('incomplete'), 'incomplete')

    def can_approve(self, user):
        return user.is_staff

    submit = Transition(
        [new, incomplete],
        pending,
        name=_('submit'),
        automatic=False
    )

    verify = Transition(
        [new, incomplete, rejected],
        verified,
        name=_('Verify'),
        automatic=False,
        permission=can_approve,
        effects=[
            NotificationEffect(PayoutAccountVerified),
            # Check if we can approve connected funding activities
        ]
    )

    rejected = Transition(
        [new, incomplete, verified],
        rejected,
        name=_('rejected'),
        automatic=False
    )

    set_incomplete = Transition(
        [new, rejected, verified],
        incomplete,
        name=_('set_incomplete'),
        automatic=False
    )
