from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment, PaymentProvider, PaymentMethod
from bluebottle.funding_pledge.transitions import PledgePaymentTransitions


class PledgePayment(Payment):
    transitions = TransitionManager(PledgePaymentTransitions, 'status')


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
