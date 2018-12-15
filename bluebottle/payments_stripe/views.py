from django.http import HttpResponse
from django.views.generic import View

import stripe

from bluebottle.payments.services import PaymentService
from bluebottle.payments_stripe.utils import get_webhook_secret
from bluebottle.payouts.models import StripePayoutAccount

from .models import StripePayment

import logging

logger = logging.getLogger(__name__)


class WebHookView(View):
    def post(self, request, **kwargs):
        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, get_webhook_secret()
            )

            if event.type == 'account.updated':
                payout_account = StripePayoutAccount.objects.get(account_id=event.data.object.id)
                payout_account.check_status()

            elif event.type == 'source.chargeable':
                payment = StripePayment.objects.get(source_token=event.data.object.id)
                service = PaymentService(payment.order_payment)
                service.adapter.charge()

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
            # Invalid signature
            return HttpResponse(status=400)

        return HttpResponse(status=200)
