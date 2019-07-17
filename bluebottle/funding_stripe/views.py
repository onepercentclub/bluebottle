from django.views.generic import View
from django.http import HttpResponse

from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.funding.authentication import DonationAuthentication
from bluebottle.funding.views import PaymentList
from bluebottle.funding.permissions import PaymentPermission
from bluebottle.funding_stripe.models import StripeSourcePayment, StripePayment, PaymentIntent
from bluebottle.funding_stripe.serializers import (
    StripeSourcePaymentSerializer, PaymentIntentSerializer
)
from bluebottle.funding_stripe.utils import stripe
from bluebottle.utils.views import (
    JsonApiViewMixin, CreateAPIView
)


class StripeSourcePaymentList(PaymentList):
    queryset = StripeSourcePayment.objects.all()
    serializer_class = StripeSourcePaymentSerializer

    authentication_classes = (
        JSONWebTokenAuthentication, DonationAuthentication,
    )

    permission_classes = (PaymentPermission, )


class StripePaymentIntentList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = PaymentIntent.objects.all()
    serializer_class = PaymentIntentSerializer

    authentication_classes = (
        JSONWebTokenAuthentication, DonationAuthentication,
    )

    permission_classes = (PaymentPermission, )


class IntentWebHookView(View):
    def post(self, request, **kwargs):
        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, stripe.webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return HttpResponse('Signature failed to verify', status=400)

        try:
            if event.type == 'payment_intent.succeeded':
                payment = self.get_payment(event.data.object.id)
                payment.transitions.succeed()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'payment_intent.payment_failed':
                payment = self.get_payment(event.data.object.id)
                payment.transitions.fail()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'charge.refunded':
                payment = self.get_payment(event.data.object.payment_intent)
                payment.transitions.refund()
                payment.save()

                return HttpResponse('Updated payment')

        except StripePayment.DoesNotExist:
            return HttpResponse('Payment not found', status=400)

    def get_payment(self, intent_id):
        intent = PaymentIntent.objects.get(intent_id=intent_id)

        try:
            return intent.payment
        except StripePayment.DoesNotExist:
            return StripePayment.objects.create(payment_intent=intent, donation=intent.donation)


class SourceWebHookView(View):
    def post(self, request, **kwargs):
        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, stripe.webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return HttpResponse('Signature failed to verify', status=400)

        try:
            if event.type == 'source.canceled':
                payment = self.get_payment_from_source(event.data.object.id)
                payment.transitions.cancel()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'source.failed':
                payment = self.get_payment_from_source(event.data.object.id)
                payment.transitions.fail()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'source.chargeable':
                payment = self.get_payment_from_source(event.data.object.id)
                payment.charge()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'charge.failed':
                payment = self.get_payment_from_charge(event.data.object.id)
                payment.transitions.fail()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'charge.succeeded':
                payment = self.get_payment_from_charge(event.data.object.id)
                payment.transitions.succeed()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'charge.refunded':
                payment = self.get_payment_from_charge(event.data.object.id)
                payment.transitions.refund()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'charge.dispute.closed' and event.data.object.status == 'lost':
                payment = self.get_payment_from_charge(event.data.object.charge)
                payment.transitions.dispute()
                payment.save()

                return HttpResponse('Updated payment')

        except StripePayment.DoesNotExist:
            return HttpResponse('Payment not found', status=400)

        return HttpResponse('Skipped')

    def get_payment_from_source(self, source_token):
        return StripeSourcePayment.objects.get(source_token=source_token)

    def get_payment_from_charge(self, charge_token):
        return StripeSourcePayment.objects.get(charge_token=charge_token)
