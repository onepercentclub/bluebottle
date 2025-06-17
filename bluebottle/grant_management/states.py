from django.utils.translation import gettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributorStateMachine
from bluebottle.fsm.state import Transition, ModelStateMachine, State, EmptyState, register
from bluebottle.funding.states import PayoutStateMachine
from bluebottle.grant_management.models import (
    GrantApplication, GrantDonor, GrantDeposit, LedgerItem, GrantPayout, GrantPayment
)


@register(GrantApplication)
class GrantApplicationStateMachine(ActivityStateMachine):
    granted = State(_("Granted"), "granted", _("The grant application was approved, now waiting bank details."))
    succeeded = State(
        _("Completed"), "completed", _("The grant application was approved and has been paid out to the applicant.")
    )

    def has_no_payouts(self):
        return (
            self.instance.payouts.count() == 0
        )

    def kyc_is_valid(self):
        return (
            self.instance.payout_account
            and self.instance.payout_account.status == "verified"
        )

    def can_approve(self, user):
        """user has the permission to approve (staff member)"""
        return user.is_staff or user.is_superuser

    def has_contributors(self):
        """has an allocation"""
        return self.instance.pk and self.instance.contributors.count()

    submit = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
        ],
        ActivityStateMachine.submitted,
        description=_("Submit the grant application for approval."),
        automatic=False,
        name=_("Submit"),
        permission=ActivityStateMachine.is_owner,
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid,
            ActivityStateMachine.initiative_is_submitted,
        ],
    )

    approve = Transition(
        [
            ActivityStateMachine.needs_work,
            ActivityStateMachine.submitted,
        ],
        granted,
        name=_('Approve'),
        description=_('Approve this application.'),
        automatic=True,
        permission=can_approve,
        conditions=[
            ActivityStateMachine.initiative_is_approved,
            ActivityStateMachine.is_valid,
            ActivityStateMachine.is_complete,
        ],
    )

    request_changes = Transition(
        [
            ActivityStateMachine.submitted
        ],
        ActivityStateMachine.needs_work,
        name=_('Needs work'),
        description=_(
            "The status of the application will be set to 'Needs work'. The activity manager "
            "can edit and resubmit the application. Don't forget to inform the activity "
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
            "Reject in case this application doesn't fit your program or the rules of the game. "
            "The activity manager will not be able to edit the application and it won't show up "
            "on the search page in the front end. The application will still be available in the "
            "back office and appear in your reporting."
        ),
        automatic=False,
        permission=ActivityStateMachine.is_staff,
    )

    succeed = Transition(
        [
            granted,
        ],
        succeeded,
        name=_('Complete'),
        description=_("The grant application has been completed and the payout has been made."),
        automatic=True,
    )

    cancel = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
            ActivityStateMachine.submitted,
            ActivityStateMachine.open,
        ],
        ActivityStateMachine.cancelled,
        name=_('Cancel'),
        description=_("The grant application has been cancelled and it will no longer be up for review."),
        automatic=False,
    )


@register(GrantDonor)
class GrantDonorStateMachine(ContributorStateMachine):

    succeed = Transition(
        [
            ContributorStateMachine.new,
            ContributorStateMachine.failed,
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


@register(GrantPayment)
class GrantPaymentStateMachine(ModelStateMachine):
    new = State(_("New"), "new", _("The payment was created"))
    succeeded = State(
        _("Succeeded"), "succeeded", _("The payment was successful paid.")
    )
    failed = State(_("Failed"), "failed", _("The payment failed."))

    succeed = Transition(
        [new, succeeded, failed],
        succeeded,
        name=_("Succeed"),
        description=_("The payment was successful."),
    )

    initiate = Transition(
        EmptyState(),
        new,
        name=_("Initiate"),
        description=_("The payment was created."),
    )

    fail = Transition(
        [new, succeeded, failed],
        failed,
        name=_("Fail"),
        description=_("The payment failed."),
    )

    reset = Transition(
        [new, succeeded, failed],
        new,
        name=_("Reset"),
        description=_("Reset the payment to new."),
    )


@register(GrantPayout)
class GrantPayoutStateMachine(PayoutStateMachine):
    pass


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


@register(GrantDeposit)
class GrantDepositStateMachine(ModelStateMachine):
    pending = State(
        _('pending'),
        'pending',
        _('The deposit is pending')
    )

    finished = State(
        _('finished'),
        'finished',
        _('The deposit is finished')
    )

    initiate = Transition(
        EmptyState(),
        pending
    )

    complete = Transition(
        pending,
        finished,
        description=_("Complete the deposit"),
        automatic=True,
        name=_("complete"),
    )


@register(LedgerItem)
class LedgerItemStateMachine(ModelStateMachine):
    pending = State(
        _('Pending'),
        'pending',
        _('The ledger item is waiting for confirmation')
    )

    final = State(
        _('Final'),
        'final',
        _('The ledger item is finalised')
    )

    removed = State(
        _('removed'),
        'removed',
        _('The ledger item is removed from the ledget')
    )

    initiate = Transition(
        EmptyState(),
        pending,
        automatic=True
    )

    finalise = Transition(
        [pending],
        final,
        description=_("Finalise the ledger item."),
        automatic=True,
        name=_("Finalise"),
    )

    remove = Transition(
        [pending],
        removed,
        description=_("Remove the ledger item."),
        automatic=True,
        name=_("Remove"),
    )
