from django.http.response import HttpResponse
from django.views.generic.base import View

from bluebottle.payments_lipisha.adapters import LipishaPaymentInterface


class PaymentInitiateView(View):

    permanent = False
    query_string = True
    pattern_name = 'lipisha-payment-initiate'

    def post(self, request):

        if request.POST['transaction_type'] == 'Payment':

            interface = LipishaPaymentInterface()
            payment_response = interface.initiate_payment(request.POST)
            # Hand order/payment over to Adapter to handle it normally

        data = payment_response

        return HttpResponse(data)


class PaymentAcknowledgeView(View):

    permanent = False
    query_string = True
    pattern_name = 'lipisha-payment-acknowledge'
