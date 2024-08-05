import json
from builtins import str

from django.db import connection
from django.http import HttpResponse
from django.views.generic import View
from moneyed import Money
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.funding.authentication import DonorAuthentication, ClientSecretAuthentication
from bluebottle.funding.models import Donor
from bluebottle.funding.permissions import PaymentPermission
from bluebottle.funding.serializers import BankAccountSerializer
from bluebottle.funding.views import PaymentList
from bluebottle.funding_stripe.models import (
    StripePayment, StripePayoutAccount, ExternalAccount
)
from bluebottle.funding_stripe.models import StripeSourcePayment, PaymentIntent
from bluebottle.funding_stripe.serializers import (
    StripeSourcePaymentSerializer, PaymentIntentSerializer,
    ConnectAccountSerializer,
    StripePaymentSerializer, ConnectAccountSessionSerializer
)
from bluebottle.funding_stripe.utils import get_stripe
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, JsonApiViewMixin, CreateAPIView, RetrieveAPIView, ListCreateAPIView,
)


class StripeSourcePaymentList(PaymentList):
    queryset = StripeSourcePayment.objects.all()
    serializer_class = StripeSourcePaymentSerializer

    authentication_classes = (
        JSONWebTokenAuthentication, DonorAuthentication,
    )

    permission_classes = (PaymentPermission,)


class AccountSession(View):
    def post(self, request):
        stripe = get_stripe()
        try:
            account = stripe.Account.create(
                type='custom',
                country='NL',
                email=request.user.email,
                business_type='individual',
                business_profile={
                    'url': 'https://goodup.com',
                    'mcc': '8398'
                },
                metadata={
                    "tenant_name": connection.tenant.client_name,
                    "tenant_domain": connection.tenant.domain_url,
                    "member_id": request.user.pk,
                },
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
            )
            account_session = stripe.AccountSession.create(
                account=account.id,
                components={
                    "account_onboarding": {
                        "enabled": True,
                        "features": {
                            "external_account_collection": True
                        },

                    },
                    "payments": {
                        "enabled": True,
                        "features": {
                            "refund_management": True,
                            "dispute_management": True,
                            "capture_payments": True
                        }
                    },
                },
            )
            print('Account created: ', account.id)
            print('Account session created: ', account_session.client_secret)
            return HttpResponse(json.dumps({'client_secret': account_session.client_secret}), status=200)

        except Exception as e:
            print('An error occurred when calling the Stripe API to create an account session: ', e)
            return HttpResponse(json.dumps({'error': str(e)}), status=500)


class StripePaymentIntentList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = PaymentIntent.objects.all()
    serializer_class = PaymentIntentSerializer

    authentication_classes = (
        JSONWebTokenAuthentication, ClientSecretAuthentication,
    )

    permission_classes = (PaymentPermission,)


class StripePaymentIntentDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveAPIView):
    queryset = PaymentIntent.objects.all()
    serializer_class = PaymentIntentSerializer

    permission_classes = []

    lookup_field = 'intent_id'

    def get_object(self):
        obj = super().get_object()
        payment = obj.get_payment()
        payment.update()
        obj.refresh_from_db()
        return obj


class StripePaymentList(PaymentList):
    queryset = StripePayment.objects.all()
    serializer_class = StripePaymentSerializer


class ConnectAccountList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = StripePayoutAccount.objects.all()
    serializer_class = ConnectAccountSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'external_accounts': ['external_accounts'],
    }

    permission_classes = (IsAuthenticated, IsOwner,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        return self.queryset.order_by('-created').filter(owner=self.request.user)


class ConnectAccountDetails(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = StripePayoutAccount.objects.all()
    serializer_class = ConnectAccountSerializer

    permission_classes = (IsAuthenticated, IsOwner,)

    prefetch_for_includes = {
        'owner': ['owner'],
        'external_accounts': ['external_accounts'],
    }

    def perform_update(self, serializer):
        token = serializer.validated_data.pop('token')
        if token:
            stripe = get_stripe()
            try:
                serializer.instance.update(token)
            except stripe.error.InvalidRequestError as e:
                try:
                    field = e.param.replace('[', '/').replace(']', '')
                    raise serializers.ValidationError(
                        {field: [e.message]}
                    )
                except AttributeError:
                    raise serializers.ValidationError(str(e))

        serializer.save()
        serializer.instance.check_status()


class ConnectAccountSession(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = StripePayoutAccount.objects.all()
    serializer_class = ConnectAccountSessionSerializer

    # permission_classes = (IsAuthenticated, IsOwner,)

    def get(self, request, *args, **kwargs):
        payout_account = self.get_object()
        stripe = get_stripe()

        try:
            account_session = stripe.AccountSession.create(
                account=payout_account.account_id,
                components={
                    "account_onboarding": {
                        "enabled": True,
                        "features": {
                            "external_account_collection": True
                        },

                    },
                    "payments": {
                        "enabled": True,
                        "features": {
                            "refund_management": True,
                            "dispute_management": True,
                            "capture_payments": True
                        }
                    },
                },
            )
            print('Account session created: ', account_session.client_secret)
            return HttpResponse(json.dumps({'client_secret': account_session.client_secret}), status=200)

        except Exception as e:
            print('An error occurred when calling the Stripe API to create an account session: ', e)
            return HttpResponse(json.dumps({'error': str(e)}), status=500)


class ExternalAccountList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
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

    def get_queryset(self):
        return self.queryset.order_by('-created').filter(connect_account__owner=self.request.user)


class ExternalAccountDetails(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
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


class IntentWebHookView(View):
    def post(self, request, **kwargs):
        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']
        stripe = get_stripe()
        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, stripe.webhook_secret_intents
            )
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return HttpResponse('Signature failed to verify', status=400)

        try:
            if event.type == 'payment_intent.succeeded':
                payment = self.get_payment(event.data.object.id)
                if payment.status != payment.states.succeeded.value:
                    payment.states.succeed()
                    try:
                        # Check if it's an old webhook call or a new one
                        transfer = stripe.Transfer.retrieve(event.data.object.charges.data[0].transfer)
                        # Fix this if we're going to support currencies that don't have smaller units, like yen.
                        payment.donation.payout_amount = Money(
                            transfer.amount / 100.0, transfer.currency
                        )
                    except AttributeError:
                        # Fix this if we're going to support currencies that don't have smaller units, like yen.
                        payment.donation.payout_amount = Money(
                            event.data.object.amount / 100.0, event.data.object.currency
                        )
                    payment.donation.save()
                    payment.save()

                return HttpResponse('Updated payment')

            elif event.type == 'payment_intent.payment_failed':
                payment = self.get_payment(event.data.object.id)
                if payment.status != payment.states.failed.value:
                    payment.states.fail(save=True)

                return HttpResponse('Updated payment')

            elif event.type == 'charge.refunded':
                if not event.data.object.payment_intent:
                    return HttpResponse('Not an intent payment')

                payment = self.get_payment(event.data.object.payment_intent)
                payment.states.refund(save=True)

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
            try:
                intent.donation.payment.payment_intent = intent
                intent.donation.payment.save()
                return intent.payment
            except Donor.payment.RelatedObjectDoesNotExist:
                payment = StripePayment.objects.create(payment_intent=intent, donation=intent.donation)
                return payment


class SourceWebHookView(View):
    def post(self, request, **kwargs):
        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']
        stripe = get_stripe()

        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, stripe.webhook_secret_sources
            )
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return HttpResponse('Signature failed to verify', status=400)

        try:
            if event.type == 'source.canceled':
                payment = self.get_payment_from_source(event.data.object.id)
                payment.states.cancel(save=True)
                return HttpResponse('Updated payment')

            if event.type == 'source.failed':
                payment = self.get_payment_from_source(event.data.object.id)
                if payment.status != payment.states.failed.value:
                    payment.states.fail(save=True)

                return HttpResponse('Updated payment')

            if event.type == 'source.chargeable':
                payment = self.get_payment_from_source(event.data.object.id)
                payment.do_charge()
                payment.save()

                return HttpResponse('Updated payment')

            if event.type == 'charge.failed':
                if event.data.object.payment_intent:
                    return HttpResponse('Not a source payment')
                payment = self.get_payment_from_charge(event.data.object.id)
                if payment.status != payment.states.failed.value:
                    payment.states.fail(save=True)

                return HttpResponse('Updated payment')

            if event.type == 'charge.succeeded':
                if event.data.object.payment_intent:
                    return HttpResponse('Not a source payment')
                payment = self.get_payment_from_charge(event.data.object.id)
                if payment.status != payment.states.succeeded.value:
                    transfer = stripe.Transfer.retrieve(event.data.object.transfer)
                    payment.donation.payout_amount = Money(
                        transfer.amount / 100.0, transfer.currency
                    )
                    payment.donation.save()
                    payment.states.succeed(save=True)

                return HttpResponse('Updated payment')

            if event.type == 'charge.pending':
                if event.data.object.payment_intent:
                    return HttpResponse('Not a source payment')
                payment = self.get_payment_from_charge(event.data.object.id)
                payment.states.authorize(save=True)
                return HttpResponse('Updated payment')

            if event.type == 'charge.refunded':
                if event.data.object.payment_intent:
                    return HttpResponse('Not a source payment')
                payment = self.get_payment_from_charge(event.data.object.id)
                payment.states.refund(save=True)

                return HttpResponse('Updated payment')

            if event.type == 'charge.dispute.closed' and event.data.object.status == 'lost':
                if event.data.object.payment_intent:
                    return HttpResponse('Not a source payment')
                payment = self.get_payment_from_charge(event.data.object.charge)
                payment.states.dispute(save=True)
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
        stripe = get_stripe()

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
                # Bust cached account
                if account.account:
                    del account.account
                account.check_status()
                account.save()

                return HttpResponse('Updated payment')
            else:
                return HttpResponse('Skipped event {}'.format(event.type))

        except StripePayoutAccount.DoesNotExist:
            return HttpResponse('Payment not found', status=400)

    def get_account(self, account_id):
        return StripePayoutAccount.objects.get(account_id=account_id)
