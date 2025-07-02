from bluebottle.fsm.effects import Effect
from django.utils.translation import gettext as _


class DisburseFundsEffect(Effect):
    conditions = []
    title = _('Disburse grant payment to grant application accounts')
    template = 'admin/disburse_funds_effect.html'

    def post_save(self, **kwargs):
        for payout in self.instance.payouts.all():
            payout.transfer_to_account()

    def __str__(self):
        return _('Disburse funds to grant application accounts')
