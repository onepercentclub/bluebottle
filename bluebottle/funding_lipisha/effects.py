from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.funding_lipisha.utils import generate_payout_account, generate_mpesa_account


class GenerateLipishaAccountsEffect(Effect):
    conditions = []
    title = _('Generate Lipisha accounts')
    template = 'admin/generate_lipisha_accounts_effect.html'

    def post_save(self, **kwargs):
        account = self.instance
        if not self.instance.mpesa_code:
            self.instance.mpesa_code = generate_mpesa_account(
                name=account.account_name
            )
            self.instance.save()
        if not self.instance.payout_code:
            self.instance.payout_code = generate_payout_account(
                name=account.account_name,
                number=account.account_number,
                bank_name=account.bank_name,
                bank_branch=account.branch_name,
                bank_address=account.address,
                swift_code=account.swift
            )
            self.instance.save()

    def __str__(self):
        return _('Generate Lipisha accounts to receive a MPESA code.')
