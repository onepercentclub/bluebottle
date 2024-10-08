from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributorStateMachine, ContributionStateMachine
from bluebottle.fsm.state import Transition, ModelStateMachine, State, AllStates, EmptyState, register
from bluebottle.funding.models import Funding, Donor, Payment, Payout, PlainPayoutAccount, MoneyContribution


@register(Funding)
class FundingStateMachine(ActivityStateMachine):
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
    on_hold = State(
        _('on_hold'),
        'on_hold',
        _("The activity is on-hold until KYC is completed")
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

    def kyc_is_valid(self):
        return (
            self.instance.payout_account
            and self.instance.payout_account.status == "verified"
        )

    submit = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.submitted,
        description=_("Submit the activity for approval."),
        automatic=False,
        name=_("Submit"),
        permission=ActivityStateMachine.is_owner,
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid,
            ActivityStateMachine.initiative_is_submitted,
            kyc_is_valid,
        ],
    )

    approve = Transition(
        [
            ActivityStateMachine.needs_work,
            ActivityStateMachine.submitted,
            on_hold
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
        permission=ActivityStateMachine.is_owner,
        conditions=[no_donations],
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

    put_on_hold = Transition(
        [
            ActivityStateMachine.open,
        ],
        on_hold,
        name=_('Put on hold'),
        description=_(
            'The campaign will not be able to receive donations'),
        automatic=True,
        permission=can_approve,
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
    )

    expire = Transition(
        [
            ActivityStateMachine.open,
        ],
        ActivityStateMachine.cancelled,
        name=_('Expire'),
        description=_(
            "The campaign didn't receive any donations before the deadline and is cancelled."),
        automatic=True,
        conditions=[
            no_donations,
        ],
    )

    extend = Transition(
        [
            ActivityStateMachine.succeeded,
            partially_funded,
            ActivityStateMachine.cancelled,
        ],
        ActivityStateMachine.open,
        name=_('Extend'),
        description=_(
            "The campaign will be extended and can receive more donations."),
        automatic=True,
        conditions=[
            without_approved_payouts,
            deadline_in_future
        ],
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
    )

    recalculate = Transition(
        [
            ActivityStateMachine.succeeded,
            partially_funded
        ],
        ActivityStateMachine.succeeded,
        name=_('Recalculate'),
        description=_(
            "The amount of donations received has changed and the payouts will be recalculated."),
        automatic=False,
        permission=ActivityStateMachine.is_staff,
        conditions=[
            target_reached
        ],
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
    )

    refund = Transition(
        [
            ActivityStateMachine.succeeded,
            partially_funded
        ],
        refunded,
        name=_('Refund'),
        description=_(
            "The campaign will be refunded and all donations will be returned to the donors."),
        automatic=False,
        permission=ActivityStateMachine.is_staff,
        conditions=[
            psp_allows_refunding,
            without_approved_payouts
        ],
    )


@register(Donor)
class DonorStateMachine(ContributorStateMachine):
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

    expired = State(_('expired'), 'expired')

    def is_successful(self):
        """donation is successful"""
        return self.instance.status == ContributorStateMachine.succeeded

    succeed = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.failed,
            expired
        ],
        ContributorStateMachine.succeeded,
        name=_('Succeed'),
        description=_("The donation has been completed"),
        automatic=True,
    )

    fail = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.succeeded
        ],
        ContributorStateMachine.failed,
        name=_('Fail'),
        description=_("The donation failed."),
        automatic=True,
    )

    refund = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.succeeded,
        ],
        refunded,
        name=_('Refund'),
        description=_("Refund this donation."),
        automatic=True,
    )

    activity_refund = Transition(
        ContributorStateMachine.succeeded,
        activity_refunded,
        name=_('Activity refund'),
        description=_(
            "Refund the donation, because the entire activity will be refunded."),
        automatic=True,
    )

    expire = Transition(
        [ContributorStateMachine.new],
        expired,
        name=_('Expire'),
        description=_("Expire the donation account. This happens when a donation is still 'new' after 10 days"),
        automatic=True
    )


@register(Payment)
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
            DonorStateMachine.refunded.value,
            DonorStateMachine.activity_refunded.value,
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
        description=_("Payment has been authorised."),
        automatic=True,
    )

    succeed = Transition(
        [new, pending, failed, refund_requested],
        succeeded,
        name=_('Succeed'),
        description=_("Payment has been completed."),
        automatic=True,
    )

    fail = Transition(
        AllStates(),
        failed,
        name=_('Fail'),
        description=_("Payment failed."),
        automatic=True,
    )

    request_refund = Transition(
        succeeded,
        refund_requested,
        name=_('Request refund'),
        description=_("Request to refund the payment."),
        automatic=False,
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
    )


@register(Payout)
class PayoutStateMachine(ModelStateMachine):
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
        description=_(
            "Approve the payout so it will be scheduled for execution."),
        automatic=False,
    )

    schedule = Transition(
        AllStates(),
        scheduled,
        name=_('Schedule'),
        description=_("Schedule payout. Triggered by payout app."),
        automatic=True,
    )

    start = Transition(
        AllStates(),
        started,
        name=_('Start'),
        description=_("Start payout. Triggered by payout app."),
        automatic=True,
    )

    reset = Transition(
        AllStates(),
        new,
        name=_('Reset'),
        description=_("Payout was rejected by the payout app. "
                      "Adjust information as needed an approve the payout again."),
        automatic=True,
    )

    succeed = Transition(
        AllStates(),
        succeeded,
        name=_('Succeed'),
        description=_("Payout was successful. Triggered by payout app."),
        automatic=True,
    )

    fail = Transition(
        AllStates(),
        failed,
        name=_('Fail'),
        description=_("Payout was not successful. "
                      "Contact support to resolve the issue."),
        automatic=True,
    )


class BankAccountStateMachine(ModelStateMachine):
    verified = State(
        _('verified'),
        'verified',
        _("Bank account is verified")
    )
    incomplete = State(
        _('incomplete'),
        'incomplete',
        _("Bank account details are missing or incorrect")
    )
    unverified = State(
        _('unverified'),
        'unverified',
        _("Bank account still needs to be verified")
    )
    rejected = State(
        _('rejected'),
        'rejected',
        _("Bank account is rejected")
    )

    initiate = Transition(
        EmptyState(),
        unverified,
        name=_("Initiate"),
        description=_("Bank account details are entered.")
    )

    request_changes = Transition(
        [verified, unverified],
        incomplete,
        name=_('Request changes'),
        description=_("Bank account is missing details"),
        automatic=False
    )

    reject = Transition(
        [verified, unverified, incomplete],
        rejected,
        name=_('Reject'),
        description=_("Reject bank account"),
        automatic=False
    )

    verify = Transition(
        [incomplete, unverified],
        verified,
        name=_('Verify'),
        description=_("Verify that the bank account is complete."),
        automatic=False
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
        [new, incomplete, rejected, verified],
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
        permission=can_approve
    )

    reject = Transition(
        [new, incomplete, verified, pending],
        rejected,
        name=_('Reject'),
        description=_("Reject the payout account."),
        automatic=False
    )

    set_incomplete = Transition(
        [pending, verified],
        incomplete,
        name=_('Set incomplete'),
        description=_(
            "Mark the payout account as incomplete. The initiator will have to add more information."),
        automatic=False
    )


@register(PlainPayoutAccount)
class PlainPayoutAccountStateMachine(PayoutAccountStateMachine):
    model = PlainPayoutAccount
    verify = Transition(
        [
            PayoutAccountStateMachine.new,
            PayoutAccountStateMachine.pending,
            PayoutAccountStateMachine.incomplete,
            PayoutAccountStateMachine.rejected
        ],
        PayoutAccountStateMachine.verified,
        name=_('Verify'),
        description=_("Verify the KYC account. You will hereby confirm that you verified the users identity."),
        automatic=False,
        permission=PayoutAccountStateMachine.can_approve
    )
    reject = Transition(
        [
            PayoutAccountStateMachine.new,
            PayoutAccountStateMachine.incomplete,
            PayoutAccountStateMachine.verified
        ],
        PayoutAccountStateMachine.rejected,
        name=_('Reject'),
        description=_("Reject the payout account. The uploaded ID scan "
                      "will be removed with this step."),
        automatic=False
    )


@register(MoneyContribution)
class DonationStateMachine(ContributionStateMachine):
    pass
