from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import Effect
from bluebottle.grant_management.models import GrantApplication, GrantPayout
from bluebottle.grant_management.models import LedgerItem, LedgerItemChoices


class DisburseFundsEffect(Effect):
    conditions = []
    title = _('Disburse grant payment to grant application accounts')
    template = 'admin/disburse_funds_effect.html'

    def post_save(self, **kwargs):
        for payout in self.instance.payouts.all():
            payout.transfer_to_account()

    def __str__(self):
        return _('Disburse funds to grant application accounts')


class GenerateDepositLedgerItem(Effect):
    def post_save(self):
        ledger_item = LedgerItem(
            fund=self.instance.fund,
            amount=self.instance.amount,
            object=self.instance,
            type=LedgerItemChoices.debit
        )
        ledger_item.states.initiate()
        ledger_item.states.finalise(save=True)

        self.instance.ledger_item = ledger_item
        self.instance.save()


class PrepareGrantApplicationPayoutsEffect(Effect):
    title = _("Create payouts for connected grant applications that where granted")
    template = "admin/create_grant_application_payouts.html"

    def post_save(self, **kwargs):
        applications = GrantApplication.objects.filter(
            status="granted",
            bank_account__connect_account=self.instance
        )

        for application in applications:
            GrantPayout.generate(application)

    def __str__(self):
        return "Create payouts for a connected grant application that was granted"


class CreatePayoutEffect(Effect):
    title = _("Create payout grant applications")
    template = "admin/create_grant_application_payouts.html"

    def post_save(self, **kwargs):
        GrantPayout.generate(self.instance)

    @property
    def is_valid(self):
        return (
            self.instance.bank_account and
            self.instance.bank_account.connect_account.status == 'verified'
        )

    def __str__(self):
        return "Create payout grant applications"


class GenerateGrantPaymentEffect(Effect):
    conditions = []
    title = _("Generate grant payment")
    template = "admin/generate_grant_payment_effect.html"

    def post_save(self, **kwargs):
        self.instance.create_payment()
