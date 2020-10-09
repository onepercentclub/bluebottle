from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine
from bluebottle.follow.effects import FollowActivityEffect, UnFollowActivityEffect
from bluebottle.fsm.effects import (
    TransitionEffect,
    RelatedTransitionEffect
)
from bluebottle.fsm.state import Transition, ModelStateMachine, State, AllStates, EmptyState
from bluebottle.funding.effects import GeneratePayoutsEffect, GenerateDonationWallpostEffect, \
    RemoveDonationWallpostEffect, UpdateFundingAmountsEffect, RefundPaymentAtPSPEffect, SetDeadlineEffect, \
    DeletePayoutsEffect, \
    SubmitConnectedActivitiesEffect, SubmitPayoutEffect, SetDateEffect, DeleteDocumentEffect, \
    ClearPayoutDatesEffect, RemoveDonationFromPayoutEffect
from bluebottle.funding.messages import (
    DonationSuccessActivityManagerMessage, DonationSuccessDonorMessage,
    FundingPartiallyFundedMessage, FundingExpiredMessage, FundingRealisedOwnerMessage,
    PayoutAccountVerified, PayoutAccountRejected,
    DonationRefundedDonorMessage, DonationActivityRefundedDonorMessage,
    FundingRejectedMessage, FundingRefundedMessage, FundingExtendedMessage,
    FundingCancelledMessage, FundingApprovedMessage

)
from bluebottle.funding.models import Funding, Donation, Payout, PlainPayoutAccount
from bluebottle.notifications.effects import NotificationEffect


class FundingStateMachine(ActivityStateMachine):
    model = Funding

    partially_funded = State(
        _('partially funded'),
        'partially_funded',
        _("The campaign has ended and received donations but didn't reach the target.")
    )
    refunded = State(
        _('refunded'),
        'refunded',
        _("The campaign has ended and all donations have been refunded.")
    )
    cancelled = State(
        _('cancelled'),
        'cancelled',
        _("The activity has ended without any donations.")
    )

    def should_finish(self):
        """the deadline has passed"""
        return self.instance.deadline and self.instance.deadline < timezone.now()

    def deadline_in_future(self):
        """the deadline is in the future"""
        if self.instance.deadline:
            return self.instance.deadline > timezone.now()
        return bool(self.instance.duration)

    def target_reached(self):
        """target amount has been reached (100% or more)"""
        if not self.instance.target:
            return False
        return self.instance.amount_raised >= self.instance.target

    def target_not_reached(self):
        """target amount has not been reached (less then 100%, but more then 0)"""
        return self.instance.amount_raised.amount and self.instance.amount_raised < self.instance.target

    def no_donations(self):
        """no (successful) donations have been made"""
        return not self.instance.donations.filter(status='succeeded').count()

    def without_approved_payouts(self):
        """hasn't got approved payouts"""
        return not self.instance.payouts.exclude(status__in=['new', 'failed']).count()

    def can_approve(self, user):
        """user has the permission to approve (staff member)"""
        return user.is_staff

    def psp_allows_refunding(self):
        """PSP allows refunding through their API"""
        return self.instance.bank_account and \
            self.instance.bank_account.provider_class and \
            self.instance.bank_account.provider_class.refund_enabled

    submit = Transition(
        [ActivityStateMachine.draft, ActivityStateMachine.needs_work],
        ActivityStateMachine.submitted,
        automatic=False,
        name=_('Submit'),
        description=_('The campaign will be submitted for review.'),
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid,
            ActivityStateMachine.initiative_is_submitted
        ],
    )

    approve = Transition(
        [
            ActivityStateMachine.needs_work,
            ActivityStateMachine.submitted
        ],
        ActivityStateMachine.open,
        name=_('Approve'),
        description=_('The campaign will be visible in the frontend and people can donate.'),
        automatic=False,
        permission=can_approve,
        conditions=[
            ActivityStateMachine.initiative_is_approved,
            ActivityStateMachine.is_valid,
            ActivityStateMachine.is_complete
        ],
        effects=[
            RelatedTransitionEffect('organizer', 'succeed'),
            SetDateEffect('started'),
            SetDeadlineEffect,
            TransitionEffect(
                'expire',
                conditions=[should_finish]
            ),
            NotificationEffect(FundingApprovedMessage)
        ]
    )

    cancel = Transition(
        [
            ActivityStateMachine.open,
        ],
        cancelled,
        name=_('Cancel'),
        description=_(
            'Cancel if the campaign will not be executed. The activity manager '
            'will not be able to edit the campaign and it won\'t show up on the '
            'search page in the front end. The campaign will still be available '
            'in the back office and appear in your reporting.'
        ),
        automatic=False,
        conditions=[
            no_donations
        ],
        effects=[
            RelatedTransitionEffect('organizer', 'fail'),
            NotificationEffect(FundingCancelledMessage)
        ]
    )

    request_changes = Transition(
        [
            ActivityStateMachine.submitted
        ],
        ActivityStateMachine.needs_work,
        name=_('Needs work'),
        description=_(
            "The status of the campaign will be set to 'Needs work'. The activity manager "
            "can edit and resubmit the campaign. Don't forget to inform the activity "
            "manager of the necessary adjustments."
        ),
        automatic=False,
        permission=can_approve
    )

    reject = Transition(
        [
            ActivityStateMachine.submitted,
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.rejected,
        name=_('Reject'),
        description=_(
            "Reject in case this campaign doesn\'t fit your program or the rules of the game. "
            "The activity manager will not be able to edit the campaign and it won\'t show up "
            "on the search page in the front end. The campaign will still be available in the "
            "back office and appear in your reporting."
        ),
        automatic=False,
        conditions=[
            no_donations
        ],
        permission=ActivityStateMachine.is_staff,
        effects=[
            RelatedTransitionEffect('organizer', 'fail'),
            NotificationEffect(FundingRejectedMessage)
        ]
    )

    expire = Transition(
        [
            ActivityStateMachine.open,
        ],
        ActivityStateMachine.cancelled,
        name=_('Expire'),
        description=_("The campaign didn't receive any donations before the deadline and is cancelled."),
        automatic=True,
        conditions=[
            no_donations,
        ],
        effects=[
            NotificationEffect(FundingExpiredMessage),
            RelatedTransitionEffect('organizer', 'fail'),
        ]
    )

    extend = Transition(
        [
            ActivityStateMachine.succeeded,
            partially_funded,
            ActivityStateMachine.cancelled,
        ],
        ActivityStateMachine.open,
        name=_('Extend'),
        description=_("The campaign will be extended and can receive more donations."),
        automatic=True,
        conditions=[
            without_approved_payouts,
            deadline_in_future
        ],
        effects=[
            DeletePayoutsEffect,
            NotificationEffect(FundingExtendedMessage)
        ]
    )

    succeed = Transition(
        [
            ActivityStateMachine.open,
            partially_funded
        ],
        ActivityStateMachine.succeeded,
        name=_('Succeed'),
        description=_(
            "The campaign ends and received donations can be payed out. Triggered when "
            "the deadline passes."
        ),
        automatic=True,
        effects=[
            GeneratePayoutsEffect,
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
        description=_("The amount of donations received has changed and the payouts will be recalculated."),
        automatic=False,
        conditions=[
            target_reached
        ],
        effects=[
            GeneratePayoutsEffect
        ]
    )

    partial = Transition(
        [
            ActivityStateMachine.open,
            ActivityStateMachine.succeeded
        ],
        partially_funded,
        name=_('Partial'),
        description=_("The campaign ends but the target isn't reached."),
        automatic=True,
        effects=[
            GeneratePayoutsEffect,
            NotificationEffect(FundingPartiallyFundedMessage)
        ]
    )

    refund = Transition(
        [
            ActivityStateMachine.succeeded,
            partially_funded
        ],
        refunded,
        name=_('Refund'),
        description=_("The campaign will be refunded and all donations will be returned to the donors."),
        automatic=False,
        conditions=[
            psp_allows_refunding,
            without_approved_payouts
        ],
        effects=[
            RelatedTransitionEffect('donations', 'activity_refund'),
            DeletePayoutsEffect,
            NotificationEffect(FundingRefundedMessage)
        ]
    )


class DonationStateMachine(ContributionStateMachine):
    model = Donation
    refunded = State(
        _('refunded'),
        'refunded',
        _("The contribution was refunded.")
    )
    activity_refunded = State(
        _('activity refunded'),
        'activity_refunded',
        _("The contribution was refunded because the activity refunded.")
    )

    def is_successful(self):
        """donation is successful"""
        return self.instance.status == ContributionStateMachine.succeeded

    succeed = Transition(
        [
            ContributionStateMachine.new,
            ContributionStateMachine.failed
        ],
        ContributionStateMachine.succeeded,
        name=_('Succeed'),
        description=_("The donation has been completed"),
        automatic=True,
        effects=[
            NotificationEffect(DonationSuccessActivityManagerMessage),
            NotificationEffect(DonationSuccessDonorMessage),
            GenerateDonationWallpostEffect,
            FollowActivityEffect,
            UpdateFundingAmountsEffect
        ]
    )

    fail = Transition(
        [
            ContributionStateMachine.new,
            ContributionStateMachine.succeeded
        ],
        ContributionStateMachine.failed,
        name=_('Fail'),
        description=_("The donation failed."),
        automatic=True,
        effects=[
            RemoveDonationWallpostEffect,
            UpdateFundingAmountsEffect,
            RemoveDonationFromPayoutEffect
        ]
    )

    refund = Transition(
        [
            ContributionStateMachine.new,
            ContributionStateMachine.succeeded,
        ],
        refunded,
        name=_('Refund'),
        description=_("Refund this donation."),
        automatic=True,
        effects=[
            RemoveDonationWallpostEffect,
            UnFollowActivityEffect,
            UpdateFundingAmountsEffect,
            RemoveDonationFromPayoutEffect,
            NotificationEffect(DonationRefundedDonorMessage)
        ]
    )

    activity_refund = Transition(
        ContributionStateMachine.succeeded,
        activity_refunded,
        name=_('Activity refund'),
        description=_("Refund the donation, because the entire activity will be refunded."),
        automatic=True,
        effects=[
            RelatedTransitionEffect('payment', 'request_refund'),
            NotificationEffect(DonationActivityRefundedDonorMessage)
        ]
    )


class BasePaymentStateMachine(ModelStateMachine):
    new = State(
        _('new'),
        'new',
        _("Payment was started.")
    )
    pending = State(
        _('pending'),
        'pending',
        _("Payment is authorised and will probably succeed shortly.")
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _("Payment is successful.")
    )
    failed = State(
        _('failed'),
        'failed',
        _("Payment failed.")
    )
    refunded = State(
        _('refunded'),
        'refunded',
        _("Payment was refunded.")
    )
    refund_requested = State(
        _('refund requested'),
        'refund_requested',
        _("Platform requested the payment to be refunded. Waiting for payment provider the confirm the refund")
    )

    def donation_not_refunded(self):
        """donation doesn't have status refunded or activity refunded"""
        return self.instance.donation.status not in [
            DonationStateMachine.refunded.value,
            DonationStateMachine.activity_refunded.value,
        ]

    initiate = Transition(
        EmptyState(),
        new,
        name=_("Initiate"),
        description=_("Payment started.")
    )

    authorize = Transition(
        [new],
        pending,
        name=_('Authorise'),
        description=_("Payment has been authorized."),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'succeed')
        ]
    )

    succeed = Transition(
        [new, pending, failed, refund_requested],
        succeeded,
        name=_('Succeed'),
        description=_("Payment has been completed."),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'succeed')
        ]
    )

    fail = Transition(
        AllStates(),
        failed,
        name=_('Fail'),
        description=_("Payment failed."),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'fail')
        ]
    )

    request_refund = Transition(
        succeeded,
        refund_requested,
        name=_('Request refund'),
        description=_("Request to refund the payment."),
        automatic=False,
        effects=[
            RefundPaymentAtPSPEffect
        ]
    )

    refund = Transition(
        [
            new,
            succeeded,
            refund_requested
        ],
        refunded,
        name=_('Refund'),
        description=_("Payment was refunded."),
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

    new = State(
        _('new'),
        'new',
        _("Payout has been created")
    )
    approved = State(
        _('approved'),
        'approved',
        _("Payout has been approved and send to the payout app.")
    )
    scheduled = State(
        _('scheduled'),
        'scheduled',
        _("Payout has been received by the payout app.")
    )
    started = State(
        _('started'),
        'started',
        _("Payout was started.")
    )
    succeeded = State(
        _('succeeded'),
        'succeeded',
        _("Payout was completed successfully.")
    )
    failed = State(
        _('failed'),
        'failed',
        _("Payout failed.")
    )

    initiate = Transition(
        EmptyState(),
        new,
        name=_("Initiate"),
        description=_("Create the payout")
    )

    approve = Transition(
        [new, approved],
        approved,
        name=_('Approve'),
        description=_("Approve the payout so it will be scheduled for execution."),
        automatic=False,
        effects=[
            SubmitPayoutEffect,
            SetDateEffect('date_approved')
        ]
    )

    schedule = Transition(
        AllStates(),
        scheduled,
        name=_('Schedule'),
        description=_("Schedule payout. Triggered by payout app."),
        automatic=True,
        effects=[
            ClearPayoutDatesEffect
        ]
    )

    start = Transition(
        AllStates(),
        started,
        name=_('Start'),
        description=_("Start payout. Triggered by payout app."),
        automatic=True,
        effects=[
            SetDateEffect('date_started')
        ]
    )

    reset = Transition(
        AllStates(),
        new,
        name=_('Reset'),
        description=_("Payout was rejected by the payout app. "
                      "Adjust information as needed an approve the payout again."),
        automatic=True,
        effects=[
            ClearPayoutDatesEffect
        ]
    )

    succeed = Transition(
        AllStates(),
        succeeded,
        name=_('Succeed'),
        description=_("Payout was successful. Triggered by payout app."),
        automatic=True,
        effects=[
            SetDateEffect('date_completed')
        ]
    )

    fail = Transition(
        AllStates(),
        failed,
        name=_('Fail'),
        description=_("Payout was not successful. "
                      "Contact support to resolve the issue."),
        automatic=True,
    )


class PayoutAccountStateMachine(ModelStateMachine):
    new = State(
        _('new'),
        'new',
        _("Payout account was created.")
    )
    pending = State(
        _('pending'),
        'pending',
        _("Payout account is pending verification.")
    )
    verified = State(
        _('verified'),
        'verified',
        _("Payout account has been verified.")
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _("Payout account was rejected.")
    )
    incomplete = State(
        _('incomplete'),
        'incomplete',
        _("Payout account is missing information or documents.")
    )

    def can_approve(self, user=None):
        """is staff user"""
        return not user or user.is_staff

    def is_reviewed(self):
        """has been verified"""
        return self.instance.reviewed

    def is_unreviewed(self):
        """has not been verified"""
        return not self.instance.reviewed

    initiate = Transition(
        EmptyState(),
        new,
        name=_("Initiate"),
        description=_("Payout account has been created")
    )

    submit = Transition(
        [new, incomplete],
        pending,
        name=_('Submit'),
        description=_("Submit payout account for review."),
        automatic=False
    )

    verify = Transition(
        [new, incomplete, rejected, pending],
        verified,
        name=_('Verify'),
        description=_("Verify the payout account."),
        automatic=False,
        permission=can_approve,
        effects=[
            NotificationEffect(PayoutAccountVerified),
            SubmitConnectedActivitiesEffect
        ]
    )

    reject = Transition(
        [new, incomplete, verified, pending],
        rejected,
        name=_('Reject'),
        description=_("Reject the payout account."),
        automatic=False,
        effects=[
            NotificationEffect(PayoutAccountRejected)
        ]
    )

    set_incomplete = Transition(
        [new, pending, rejected, verified],
        incomplete,
        name=_('Set incomplete'),
        description=_("Mark the payout account as incomplete. The initiator will have to add more information."),
        automatic=False
    )


class PlainPayoutAccountStateMachine(PayoutAccountStateMachine):
    model = PlainPayoutAccount

    verify = Transition(
        [
            PayoutAccountStateMachine.new,
            PayoutAccountStateMachine.incomplete,
            PayoutAccountStateMachine.rejected
        ],
        PayoutAccountStateMachine.verified,
        name=_('Verify'),
        description=_("Verify the payout account."),
        automatic=False,
        permission=PayoutAccountStateMachine.can_approve,
        effects=[
            NotificationEffect(PayoutAccountVerified),
            SubmitConnectedActivitiesEffect,
            DeleteDocumentEffect
        ]
    )

    reject = Transition(
        [
            PayoutAccountStateMachine.new,
            PayoutAccountStateMachine.incomplete,
            PayoutAccountStateMachine.verified
        ],
        PayoutAccountStateMachine.rejected,
        name=_('Reject'),
        description=_("Reject the payout account."),
        automatic=False,
        effects=[
            NotificationEffect(PayoutAccountRejected),
            DeleteDocumentEffect
        ]
    )
