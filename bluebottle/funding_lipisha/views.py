import logging

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.generic import View

from bluebottle.funding.views import PaymentList
from bluebottle.funding_lipisha.adapters import LipishaPaymentInterface
from bluebottle.funding_lipisha.models import LipishaPayment
from bluebottle.funding_lipisha.serializers import LipishaPaymentSerializer
from bluebottle.funding_lipisha.utils import initiate_push_payment
from bluebottle.funding.exception import PaymentException

logger = logging.getLogger(__name__)


class LipishaPaymentList(PaymentList):
    queryset = LipishaPayment.objects.all()
    serializer_class = LipishaPaymentSerializer

    def perform_create(self, serializer):
        payment = serializer.save()
        payment = initiate_push_payment(payment)
        return payment

    def post(self, request, **kwargs):
        try:
            return super(LipishaPaymentList, self).post(request, **kwargs)
        except PaymentException as e:
            return HttpResponseBadRequest('Error creating payment: {}'.format(e))


class LipishaWebHookView(View):

    permanent = False
    query_string = True

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
