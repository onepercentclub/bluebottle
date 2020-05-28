from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import (
    TransitionEffect,
    RelatedTransitionEffect
)
from bluebottle.fsm.state import Transition, ModelStateMachine, State, AllStates, EmptyState
from bluebottle.funding.effects import GeneratePayouts, GenerateDonationWallpost, \
    RemoveDonationWallpost, UpdateFundingAmounts, RefundPaymentAtPSP, SetStartDate, SetDeadline, DeletePayouts, \
    SubmitConnectedActivities
from bluebottle.funding.messages import DonationSuccessActivityManagerMessage, DonationSuccessDonorMessage, \
    FundingPartiallyFundedMessage, FundingClosedMessage, FundingRealisedOwnerMessage, PayoutAccountVerified, \
    PayoutAccountRejected, DonationRefundedDonorMessage
from bluebottle.funding.models import Funding, Donation, Payout, PlainPayoutAccount
from bluebottle.notifications.effects import NotificationEffect


class FundingStateMachine(ActivityStateMachine):
    model = Funding

    partially_funded = State(_('partially funded'), 'partially_funded')
    refunded = State(_('refunded'), 'refunded')

    def should_finish(self):
        """the deadline has passed"""
        return self.instance.deadline and self.instance.deadline < timezone.now()

    def deadline_in_future(self):
        if self.instance.deadline:
            return self.instance.deadline > timezone.now()
        return bool(self.instance.duration)

    def target_reached(self):
        return self.instance.amount_raised >= self.instance.target

    def target_not_reached(self):
        return self.instance.amount_raised.amount and self.instance.amount_raised < self.instance.target

    def no_donations(self):
        return not self.instance.donations.filter(status='succeeded').count()

    def without_approved_payouts(self):
        return not self.instance.payouts.exclude(status__in=['new', 'failed']).count()

    def can_approve(self, user):
        return user.is_staff

    approve = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
            ActivityStateMachine.submitted
        ],
        ActivityStateMachine.open,
        name=_('Approve'),
        automatic=False,
        permission=can_approve,
        conditions=[
            ActivityStateMachine.initiative_is_approved,
            ActivityStateMachine.is_valid,
            ActivityStateMachine.is_complete
        ],
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

    request_changes = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.submitted
        ],
        ActivityStateMachine.needs_work,
        name=_('Request changes'),
        automatic=False,
        permission=can_approve
    )

    reject = Transition(
        [
            ActivityStateMachine.submitted,
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
            ActivityStateMachine.open,
        ],
        ActivityStateMachine.rejected,
        name=_('Reject'),
        automatic=False,
        conditions=[
            no_donations
        ],
        permission=ActivityStateMachine.is_staff,
        effects=[
            RelatedTransitionEffect('organizer', 'fail')
        ]
    )

    close = Transition(
        ActivityStateMachine.open,
        ActivityStateMachine.closed,
        name=_('Close'),
        automatic=True,
        conditions=[
            no_donations,
        ],
        effects=[
            NotificationEffect(FundingClosedMessage),
            RelatedTransitionEffect('organizer', 'fail'),
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
    activity_refunded = State(_('activity refunded'), 'activity_refunded')

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
        ContributionStateMachine.succeeded,
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
        ContributionStateMachine.succeeded,
        activity_refunded,
        name=_('Activity refund'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('payment', 'request_refund'),
            NotificationEffect(DonationRefundedDonorMessage)
        ]
    )


class BasePaymentStateMachine(ModelStateMachine):
    new = State(_('new'), 'new')
    pending = State(_('pending'), 'pending')
    succeeded = State(_('succeeded'), 'succeeded')
    failed = State(_('failed'), 'failed')
    refunded = State(_('refunded'), 'refunded')
    refund_requested = State(_('refund requested'), 'refund_requested')

    def donation_not_refunded(self):
        return self.instance.donation.status not in [
            DonationStateMachine.refunded.value,
            DonationStateMachine.activity_refunded.value,
        ]

    initiate = Transition(EmptyState(), new)

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
        [new, pending, failed, refund_requested],
        succeeded,
        name=_('Succeed'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'succeed')
        ]
    )

    fail = Transition(
        AllStates(),
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
        automatic=True,
        effects=[
            RelatedTransitionEffect(
                'donation', 'refund',
                conditions=[
                    donation_not_refunded
                ]
            ),
        ]
    )


class PayoutStateMachine(ModelStateMachine):
    model = Payout

    new = State(_('new'), 'new')
    approved = State(_('approve'), 'approve')
    scheduled = State(_('scheduled'), 'scheduled')
    started = State(_('started'), 'started')
    succeeded = State(_('succeeded'), 'succeeded')
    failed = State(_('failed'), 'failed')

    initiate = Transition(EmptyState(), new)

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

    new = State(_('new'), 'new')
    pending = State(_('pending'), 'pending')
    verified = State(_('verified'), 'verified')
    rejected = State(_('rejected'), 'rejected')
    incomplete = State(_('incomplete'), 'incomplete')

    def can_approve(self, user):
        return user.is_staff

    initiate = Transition(EmptyState(), new)

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
            SubmitConnectedActivities
        ]
    )

    reject = Transition(
        [new, incomplete, verified],
        rejected,
        name=_('Reject'),
        automatic=False,
        effects=[
            NotificationEffect(PayoutAccountRejected)
        ]
    )

    set_incomplete = Transition(
        [new, rejected, verified],
        incomplete,
        name=_('Set incomplete'),
        automatic=False
    )


class PlainPayoutAccountStateMachine(PayoutAccountStateMachine):

    model = PlainPayoutAccount

    def is_reviewed(self):
        return self.instance.reviewed

    def is_unreviewed(self):
        return not self.instance.reviewed
