from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.funding.models import Payout


class GeneratePayouts(Effect):
    post_save = True
    conditions = []

    def execute(self):
        Payout.generate(self.instance)

    def __unicode__(self):
        return _('Generate payouts')


class RefundDonations(Effect):
    post_save = True
    conditions = []

    def execute(self):
        for donation in self.instance.donations.filter(status__in=['succeeded']).all():
            donation.payment.transitions.request_refund()
            donation.payment.save()

    def __unicode__(self):
        return _('Refund all donations')


class CancelPayouts(Effect):
    post_save = True
    conditions = []

    def execute(self):
        for payout in self.instance.payouts.all():
            payout.states.cancel()

    def __unicode__(self):
        return _('Refund all donations')

