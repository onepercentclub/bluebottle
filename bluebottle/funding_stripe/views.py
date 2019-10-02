from django.http import HttpResponse, Http404
from django.views.generic import View
from rest_framework import serializers
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.funding.authentication import DonationAuthentication
from bluebottle.funding.permissions import PaymentPermission
from bluebottle.funding.transitions import PayoutAccountTransitions
from bluebottle.funding.views import PaymentList
from bluebottle.funding_stripe.models import (
    StripePayment, StripePayoutAccount, ExternalAccount
)
from bluebottle.funding_stripe.models import StripeSourcePayment, PaymentIntent
from bluebottle.funding_stripe.serializers import (
    StripeSourcePaymentSerializer, PaymentIntentSerializer,
    ConnectAccountSerializer,
    StripePaymentSerializer
)
from bluebottle.funding.serializers import BankAccountSerializer
from bluebottle.funding_stripe.utils import stripe
from bluebottle.members.models import Member
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, JsonApiViewMixin, CreateAPIView,
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


class StripePaymentList(PaymentList):
    queryset = StripePayment.objects.all()
    serializer_class = StripePaymentSerializer


class ConnectAccountDetails(JsonApiViewMixin, AutoPrefetchMixin, CreateModelMixin, RetrieveUpdateAPIView):
    queryset = StripePayoutAccount.objects.all()
    serializer_class = ConnectAccountSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'external_accounts': ['external_accounts'],
    }

    permission_classes = (IsAuthenticated, IsOwner, )

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get_object(self):
        try:
            # Make this smarter
            obj = self.request.user.funding_payout_account.first()
        except Member.funding_payout_account.RelatedObjectDoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        token = serializer.validated_data.pop('token')
        serializer.save(owner=self.request.user)
        if token:
            serializer.instance.update(token)

    def perform_update(self, serializer):
        token = serializer.validated_data.pop('token')
        if token:
            try:
                serializer.instance.update(token)
            except stripe.error.InvalidRequestError, e:
                field = e.param.replace('[', '/').replace(']', '')
                raise serializers.ValidationError(
                    {'account/{}'.format(field): [{'details': e.message, 'code': e.code}]}
                )
        serializer.save()


class ExternalAccountsList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    permission_classes = []

    queryset = ExternalAccount.objects.all()
    serializer_class = BankAccountSerializer

    prefetch_for_includes = {
        'connect_account': ['connect_account'],
    }

    related_permission_classes = {
        'connect_account': [IsOwner]
    }

    def perform_create(self, serializer):
        token = serializer.validated_data.pop('token')
        serializer.save()
        serializer.instance.create(token)


class ExternalAccountsDetails(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = ExternalAccount.objects.all()
    serializer_class = BankAccountSerializer

    prefetch_for_includes = {
        'connect_account': ['connect_account'],
    }

    related_permission_classes = {
        'connect_account': [IsOwner]
    }

    def perform_update(self, serializer):
        token = serializer.validated_data.pop('token')
        serializer.instance.update(token)
        serializer.save()


class WebHookView(View):
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

            elif event.type == 'payment_intent.payment_failed':
                payment = self.get_payment(event.data.object.id)
                payment.transitions.fail()
                payment.save()

                return HttpResponse('Updated payment')

            elif event.type == 'charge.refunded':
                payment = self.get_payment(event.data.object.payment_intent)
                payment.transitions.refund()
                payment.save()

                return HttpResponse('Updated payment')
            else:
                return HttpResponse('Skipped event {}'.format(event.type))

        except StripePayment.DoesNotExist:
            return HttpResponse('Payment not found', status=400)

    def get_payment(self, intent_id):
        intent = PaymentIntent.objects.get(intent_id=intent_id)

        try:
            return intent.payment
        except StripePayment.DoesNotExist:
            return StripePayment.objects.create(payment_intent=intent, donation=intent.donation)


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

            elif event.type == 'payment_intent.payment_failed':
                payment = self.get_payment(event.data.object.id)
                payment.transitions.fail()
                payment.save()

                return HttpResponse('Updated payment')

            elif event.type == 'charge.refunded':
                payment = self.get_payment(event.data.object.payment_intent)
                payment.transitions.refund()
                payment.save()

                return HttpResponse('Updated payment')
            else:
                return HttpResponse('Skipped event {}'.format(event.type))

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


class ConnectWebHookView(View):
    def post(self, request, **kwargs):

        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, stripe.webhook_secret_connect
            )
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return HttpResponse('Signature failed to verify', status=400)

        try:
            if event.type == 'account.updated':
                account = self.get_account(event.data.object.id)
                if (
                    account.status != PayoutAccountTransitions.values.verified and
                    account.verified
                ):
                    account.transitions.verify()

                if (
                    account.status != PayoutAccountTransitions.values.rejected and
                    account.disabled
                ):
                    account.transitions.reject()

                account.save()

                return HttpResponse('Updated payment')
            else:
                return HttpResponse('Skipped event {}'.format(event.type))

        except StripePayoutAccount.DoesNotExist:
            return HttpResponse('Payment not found', status=400)

    def get_account(self, account_id):
        return StripePayoutAccount.objects.get(account_id=account_id)
