from bluebottle.payments.adapters import BasePaymentAdapter

from .models import PledgeStandardPayment


class PledgePaymentAdapter(BasePaymentAdapter):

    def create_payment(self):
        # A little hacky but we can set the status to pledged here
        self.order_payment.pledged() 

    def get_authorization_action(self):
        # Return type success to indicate no further authorization is required.
        return {'type': 'success'}

    def check_payment_status(self):
        # The associated order should always be processed as pledged
        self.order_payment.pledged()