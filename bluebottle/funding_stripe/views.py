from django.views.generic import View
from django.http import HttpResponse

from bluebottle.funding.views import PaymentList
from bluebottle.funding_stripe.models import StripePayment
from bluebottle.funding_stripe.serializers import StripePaymentSerializer
from bluebottle.funding_stripe.utils import StripeMixin


class StripePaymentList(PaymentList):
    queryset = StripePayment.objects.all()
    serializer_class = StripePaymentSerializer


class WebHookView(View, StripeMixin):
    def post(self, request, **kwargs):

        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = self.stripe.Webhook.construct_event(
                payload, signature_header, self.webhook_secret
            )
        except self.stripe.error.SignatureVerificationError:
            # Invalid signature
            return HttpResponse('Signature failed to verify', status=400)

        try:
            if event.type == 'payment_intent.succeeded':
                payment = self.get_payment(event.data.object.id)
                payment.succeed()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'payment_intent.payment_failed':
                payment = self.get_payment(event.data.object.id)
                payment.fail()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'charge.refunded':
                payment = self.get_payment(event.data.object.payment_intent)
                payment.refund()
                payment.save()

                return HttpResponse('Updated payment')

        except StripePayment.DoesNotExist:
            return HttpResponse('Payment not found', status=400)

    def get_payment(self, intent_id):
        return StripePayment.objects.get(intent_id=intent_id)
