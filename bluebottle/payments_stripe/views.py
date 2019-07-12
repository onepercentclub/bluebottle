import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View

import stripe

from bluebottle.payments.exception import PaymentException
from bluebottle.payments.services import PaymentService
from .models import StripePayment

logger = logging.getLogger(__name__)


class WebHookView(View):
    def post(self, request, **kwargs):
        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, settings.STRIPE['webhook_secret']
            )

            if event.type == 'source.chargeable':
                payment = StripePayment.objects.get(source_token=event.data.object.id)

                service = PaymentService(payment.order_payment)
                service.adapter.charge()
            elif event.type == 'charge.dispute.closed' and event.data.object.status == 'lost':
                payment = StripePayment.objects.get(charge_token=event.data.object.charge)
                service = PaymentService(payment.order_payment)
                charge = stripe.Charge.retrieve(event.data.object.charge)
                service.adapter.update_from_charge(charge)
            elif event.type in ('source.canceled', 'source.failed'):
                payment = StripePayment.objects.get(source_token=event.data.object.id)
                service = PaymentService(payment.order_payment)
                service.adapter.update_from_source(event.data.object)
            elif event.type in (
                'charge.succeeded', 'charge.pending', 'charge.failed', 'charge.refunded',
            ):
                payment = StripePayment.objects.get(charge_token=event.data.object.id)
                service = PaymentService(payment.order_payment)
                service.adapter.update_from_charge(event.data.object)
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return HttpResponse(status=400)
        except StripePayment.DoesNotExist:
            # StripePayment not found
            return HttpResponse(status=400)
        except PaymentException:
            # Payment error due to failed charge e.g.
            return HttpResponse(status=200)
        return HttpResponse(status=200)
