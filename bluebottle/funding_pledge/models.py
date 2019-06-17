from bluebottle.funding.models import Payment, PaymentProvider
from django.utils.translation import ugettext_lazy as _


class PledgePayment(Payment):

    def save(self, *args, **kwargs):
        if self.status == self.Status.new:
            self.succeed()

        super(PledgePayment, self).save(*args, **kwargs)

    @Payment.status.transition(
        source=['success'],
        target='refund_requested'
    )
    def request_refund(self):
        self.refund()


class PledgePaymentProvider(PaymentProvider):

    @property
    def payment_methods(self):
        return [{
            'provider': _('Pledge'),
            'code': 'pledge',
            'name': _('pledge'),
            'currencies': []
        }]
