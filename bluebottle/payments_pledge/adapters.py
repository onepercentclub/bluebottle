from bluebottle.payments.adapters import BasePaymentAdapter

from .models import PledgeStandardPayment


class PledgePaymentAdapter(BasePaymentAdapter):

    def create_payment(self):
        # No payment is created here as it isn't needed for a pledge.

        # The associated order can be immediately processed as successful
        self.order_payment.order.succeeded()

    def get_authorization_action(self):
        # Return type success to indicate no further authorization is required.
        return {'type': 'success'}