from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect


class RefundStripePaymentAtPSP(Effect):
    post_save = True
    conditions = []

    def execute(self, **kwargs):
        intent = self.instance.payment_intent.intent
        intent.charges.data[0].refund(
            reverse_transfer=True,
        )

    def __unicode__(self):
        return _('Refund payment at Stripe')
