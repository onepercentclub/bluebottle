import logging

from django.http import JsonResponse
from django.views.generic import View

from bluebottle.funding.views import PaymentList
from bluebottle.funding_lipisha.adapters import LipishaPaymentInterface
from bluebottle.funding_lipisha.models import LipishaPayment
from bluebottle.funding_lipisha.serializers import LipishaPaymentSerializer

logger = logging.getLogger(__name__)


class LipishaPaymentList(PaymentList):
    queryset = LipishaPayment.objects.all()
    serializer_class = LipishaPaymentSerializer


class LipishaWebHookView(View):

    permanent = False
    query_string = True
    pattern_name = 'vitepay-payment-initiate'

    def post(self, request):
        if request.POST['api_type'] == 'Initiate':
            if request.POST['transaction_type'] == 'Payment':
                interface = LipishaPaymentInterface()
                payment_response = interface.initiate_payment(request.POST)
                data = payment_response
                return JsonResponse(data)
            else:
                logger.error('Could not parse Lipisha Paymnent update: '
                             'Unknown transaction_type {}'.format(request.POST['transaction_type']))
        if request.POST['api_type'] == 'Acknowledge':
            interface = LipishaPaymentInterface()
            payment_response = interface.acknowledge_payment(request.POST)
            data = payment_response
            return JsonResponse(data)
        else:
            logger.error('Could not parse Lipisha Paymnent update: '
                         'Unknown api_type {}'.format(request.POST['api_type']))
