from bluebottle.fsm import TransitionManager
from bluebottle.funding_pledge.transitions import PledgePaymentTransitions
from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod
from django.utils.translation import ugettext_lazy as _


class PledgePayment(Payment):
    transitions = TransitionManager(PledgePaymentTransitions, 'status')

    def save(self, *args, **kwargs):
        if self.status == PledgePaymentTransitions.values.new:
            self.transitions.succeed()

        super(PledgePayment, self).save(*args, **kwargs)


class PledgePaymentProvider(PaymentProvider):

    @property
    def payment_methods(self):
        return [
            PaymentMethod(
                provider='pledge',
                code='pledge',
                name=_('Pledge'),
                currencies=['EUR', 'USD']
            )
        ]
