import json
import logging

from django.http import HttpResponse, HttpResponseNotFound
from django.views.generic import View
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.funding.authentication import DonorAuthentication
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.models import Donor
from bluebottle.funding.views import PaymentList
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwaveBankAccount
from bluebottle.funding_flutterwave.serializers import FlutterwavePaymentSerializer, FlutterwaveBankAccountSerializer
from bluebottle.funding_flutterwave.utils import check_payment_status
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import ListCreateAPIView, JsonApiViewMixin, RetrieveUpdateAPIView

logger = logging.getLogger(__name__)


class FlutterwavePaymentList(PaymentList):
    queryset = FlutterwavePayment.objects.all()
    serializer_class = FlutterwavePaymentSerializer

    authentication_classes = (
        JSONWebTokenAuthentication, DonorAuthentication,
    )

    def perform_create(self, serializer):
        super(FlutterwavePaymentList, self).perform_create(serializer)
        check_payment_status(serializer.instance)


class FlutterwaveWebhookView(View):

    def post(self, request, **kwargs):
        logger.info('Flutterwave webhook: {}'.format(request.body))
        try:
            data = json.loads(request.body.decode())
        except ValueError:
            raise PaymentException('Error parsing Flutterwave webhook: {}'.format(request.body))
        try:
            # can be either tx_ref or txRef or data.tx_ref in Flutterwave responses
            if 'data' in data:
                data = data.get('data')
            tx_ref = data.get('txRef', data.get('tx_ref'))
            payment = FlutterwavePayment.objects.get(tx_ref=tx_ref)
        except (KeyError, TypeError):
            raise PaymentException('Error parsing Flutterwave webhook: {}'.format(request.body))
        except FlutterwavePayment.DoesNotExist:
            try:
                donation = Donor.objects.get(id=tx_ref)
                payment = FlutterwavePayment.objects.create(
                    donation=donation,
                    tx_ref=tx_ref
                )
                payment.save()
            except Donor.DoesNotExist:
                return HttpResponseNotFound()
        check_payment_status(payment)
        return HttpResponse(status=200)


class FlutterwaveBankAccountAccountList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = FlutterwaveBankAccount.objects.all()
    serializer_class = FlutterwaveBankAccountSerializer
    permission_classes = []

    related_permission_classes = {
        'connect_account': [IsOwner]
    }


class FlutterwaveBankAccountAccountDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = FlutterwaveBankAccount.objects.all()
    serializer_class = FlutterwaveBankAccountSerializer
    permission_classes = []

    related_permission_classes = {
        'connect_account': [IsOwner]
    }
