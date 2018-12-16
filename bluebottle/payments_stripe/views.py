import logging
import stripe

from django.http import HttpResponse
from django.views.generic import View

from bluebottle.payments.services import PaymentService
from bluebottle.payments_stripe.utils import get_webhook_secret

from .models import StripePayment


logger = logging.getLogger(__name__)


class WebHookView(View):
    def post(self, request, **kwargs):
        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, get_webhook_secret()
            )

            if event.type == 'source.chargeable':
                payment = StripePayment.objects.get(source_token=event.data.object.id)
                service = PaymentService(payment.order_payment)
                service.adapter.charge()

            elif event.type in (
                'charge.succeeded', 'charge.pending', 'charge.failed', 'charge.refunded',
            ):
                payment = StripePayment.objects.get(charge_token=event.data.object.id)
                service = PaymentService(payment.order_payment)
                service.adapter.update_from_charge(event.data.object)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)
        except StripePayment.DoesNotExist:
            # StripePayment not found
            return HttpResponse(status=400)
        return HttpResponse(status=200)
