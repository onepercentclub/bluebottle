import json

from django.http import HttpResponse
from django.views.generic import View

from bluebottle.funding.views import PaymentList
from bluebottle.funding_flutterwave.models import FlutterwavePayment
from bluebottle.funding_flutterwave.serializers import FlutterwavePaymentSerializer
from bluebottle.funding_flutterwave.utils import check_payment_status


class FlutterwavePaymentList(PaymentList):
    queryset = FlutterwavePayment.objects.all()
    serializer_class = FlutterwavePaymentSerializer


class FlutterwaveWebhookView(View):
    def post(self, request, **kwargs):
        data = json.loads(request.body)
        payment = FlutterwavePayment.objects.get(tx_ref=data['txRef'])
        check_payment_status(payment)
        return HttpResponse(status=200)
