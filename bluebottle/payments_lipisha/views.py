from django.http import JsonResponse
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
            data = payment_response
            return JsonResponse(data)


class PaymentAcknowledgeView(View):

    permanent = False
    query_string = True
    pattern_name = 'lipisha-payment-acknowledge'
