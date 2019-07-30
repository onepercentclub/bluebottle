import json

from django.http import HttpResponse, HttpResponseNotFound
from django.views.generic import View

from bluebottle.funding.models import Donation
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
        try:
            payment = FlutterwavePayment.objects.get(tx_ref=data['txRef'])
        except FlutterwavePayment.DoesNotExist:
            try:
                donation = Donation.objects.get(id=data['txRef'])
                payment = FlutterwavePayment.objects.create(
                    donation=donation,
                    tx_ref=donation.id
                )
                payment.save()
            except Donation.DoesNotExist:
                return HttpResponseNotFound()
        check_payment_status(payment)
        return HttpResponse(status=200)
