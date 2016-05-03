from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.payments.exception import PaymentException

from .models import PledgeStandardPayment


class PledgePaymentAdapter(BasePaymentAdapter):

    def create_payment(self):
        try:
            can_pledge = self.order_payment.user.can_pledge
        except:
            can_pledge = False 

        if not can_pledge:
            raise PaymentException('User does not have permission to pledge')
    
        # A little hacky but we can set the status to pledged here
        self.order_payment.pledged() 

    def get_authorization_action(self):
        # Return type success to indicate no further authorization is required.
        return {'type': 'success'}

    def check_payment_status(self):
        pass