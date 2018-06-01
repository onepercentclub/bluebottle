import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import View

from bluebottle.payments.exception import PaymentException
from bluebottle.payments.services import PaymentService
from bluebottle.payments_beyonic.models import BeyonicPayment


class PaymentResponseView(View):

    permanent = False
    query_string = True
    pattern_name = 'beyonic-payment-response'

    def post(self, request, *args, **kwargs):
        payload = json.loads(request.body)['data']
        transaction_reference = payload["collection_request"]["id"]
        payment = get_object_or_404(BeyonicPayment, transaction_reference=transaction_reference)
        service = PaymentService(payment.order_payment)
        try:
            service.check_payment_status()
            return HttpResponse('success')
        except PaymentException:
            return HttpResponse('success')
