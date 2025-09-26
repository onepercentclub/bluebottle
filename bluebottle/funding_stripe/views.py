import uuid
import logging

from django.core.exceptions import ValidationError
from django.db import connection
from django.http import HttpResponse
from django.urls.exceptions import Http404
from django.core.exceptions import PermissionDenied
from django.views.generic import View
from django_tools.middlewares.ThreadLocal import get_current_user
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from stripe import InvalidRequestError

from bluebottle.funding.authentication import (
    DonorAuthentication,
    ClientSecretAuthentication,
)
from bluebottle.funding.permissions import PaymentPermission, IntentPermission
from bluebottle.funding.models import Donor, FundingPlatformSettings
from bluebottle.funding.serializers import BankAccountSerializer
from bluebottle.funding.views import PaymentList
from bluebottle.funding_stripe.models import (
    StripePayment, StripePayoutAccount, ExternalAccount, StripePaymentProvider, STRIPE_EUROPEAN_COUNTRY_CODES
)
from bluebottle.funding_stripe.models import StripeSourcePayment, PaymentIntent
from bluebottle.funding_stripe.serializers import (
    StripeSourcePaymentSerializer,
    PaymentIntentSerializer,
    ConnectAccountSerializer,
    StripePaymentSerializer,
    ConnectAccountSessionSerializer,
    CountrySpecSerializer,
    ExternalAccountSerializer,
    BankTransferSerializer,
    ConnectVerificationLinkSerializer
)
from bluebottle.funding_stripe.utils import get_stripe
from bluebottle.grant_management.models import GrantPayment
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import (
    ListAPIView,
    RetrieveUpdateAPIView,
    JsonApiViewMixin,
    CreateAPIView,
    RetrieveAPIView,
    ListCreateAPIView,
)
from bluebottle.utils.utils import get_current_host

logger = logging.getLogger(__name__)


class StripeSourcePaymentList(PaymentList):
    queryset = StripeSourcePayment.objects.all()
    serializer_class = StripeSourcePaymentSerializer

    authentication_classes = (
        JSONWebTokenAuthentication, DonorAuthentication,
    )

    permission_classes = (PaymentPermission,)


def get_init_args(donation, ):
    statement_descriptor = connection.tenant.name[:22]

    intent_args = dict(
        amount=int(donation.amount.amount * 100),
        currency=str(donation.amount.currency),
        statement_descriptor=statement_descriptor,
        statement_descriptor_suffix=statement_descriptor[:18],
        metadata={
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
            "activity_id": donation.activity.id,
            "activity_title": donation.activity.title,
        }
    )
    return intent_args


class StripePaymentIntentList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = PaymentIntent.objects.all()
    serializer_class = PaymentIntentSerializer

    authentication_classes = (
        JSONWebTokenAuthentication, ClientSecretAuthentication,
    )

    permission_classes = (PaymentPermission,)

    def perform_create(self, serializer):
        if hasattr(serializer.Meta, 'model'):
            self.check_object_permissions(
                self.request,
                serializer.Meta.model(**serializer.validated_data)
            )
        payment_intent_data = serializer.validated_data
        donation = payment_intent_data['donation']
        connect_account = donation.activity.bank_account.connect_account
        init_args = get_init_args(donation)

        init_args['transfer_data'] = {
            'destination': connect_account.account_id,
        }
        init_args['automatic_payment_methods'] = {"enabled": True}

        payment_provider = StripePaymentProvider.objects.first()

        platform_currency = payment_provider.get_default_currency()[0].lower()

        if 'card_payments' in connect_account.account.capabilities:
            # Only do  on_behalf_of when card_payments are enabled
            if payment_provider.country != connect_account.country:
                if payment_provider.country in STRIPE_EUROPEAN_COUNTRY_CODES:
                    if connect_account.country not in STRIPE_EUROPEAN_COUNTRY_CODES:
                        # European stripe account and connect account not in Europe
                        init_args['on_behalf_of'] = connect_account.account_id
                else:
                    # Non european stripe account and countries differ
                    init_args['on_behalf_of'] = connect_account.account_id

            if platform_currency == 'usd' and connect_account.country != 'US':
                init_args['on_behalf_of'] = connect_account.account_id

        stripe = get_stripe()
        intent = stripe.PaymentIntent.create(
            **init_args
        )
        serializer.save(
            intent_id=intent.id,
            client_secret=intent.client_secret,
        )


class StripePaymentIntentDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveAPIView):
    queryset = PaymentIntent.objects.all()
    serializer_class = PaymentIntentSerializer

    authentication_classes = (
        JSONWebTokenAuthentication, DonorAuthentication,
    )
    permission_classes = [IntentPermission]

    def get_object(self):
        obj = super().get_object()
        payment = obj.get_payment()
        payment.update()
        obj.refresh_from_db()
        return obj


class StripePaymentList(PaymentList):
    queryset = StripePayment.objects.all()
    serializer_class = StripePaymentSerializer


class StripeBankTransferDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveAPIView):
    queryset = PaymentIntent.objects.all()
    serializer_class = BankTransferSerializer

    permission_classes = []

    def get_object(self):
        obj = super().get_object()
        payment = obj.get_payment()
        payment.update()
        obj.refresh_from_db()
        return obj


class StripeBankTransferList(PaymentList):
    queryset = PaymentIntent.objects.all()
    serializer_class = BankTransferSerializer

    def perform_create(self, serializer):
        # Get data from serializer without saving
        payment_intent_data = serializer.validated_data
        donation = payment_intent_data['donation']
        account_currency = str(donation.activity.bank_account.currency or 'EUR').upper()
        currency = str(donation.amount.currency)
        # Validate the currency compatibility
        if currency != account_currency:
            raise ValidationError(f'Bank transfer not supported for currency {currency} only {account_currency}')

        stripe = get_stripe()
        init_args = get_init_args(donation)
        connect_account = donation.activity.bank_account.connect_account

        bank_transfer_type = 'eu_bank_transfer'
        if currency == 'USD':
            bank_transfer_type = "us_bank_transfer"
        elif currency == 'GBP':
            bank_transfer_type = "gb_bank_transfer"
        elif currency == 'MXN':
            bank_transfer_type = "mx_bank_transfer"

        if currency == 'EUR':
            init_args['payment_method_options'] = {
                "customer_balance": {
                    "funding_type": "bank_transfer",
                    "bank_transfer": {
                        "type": bank_transfer_type,
                        "eu_bank_transfer": {"country": "NL"}
                    },
                },
            }
        else:
            init_args['payment_method_options'] = {
                "customer_balance": {
                    "funding_type": "bank_transfer",
                    "bank_transfer": {
                        "type": bank_transfer_type,
                    },
                },
            }

        # Create the customer in Stripe
        user = get_current_user()
        customer = stripe.Customer.create(
            stripe_account=connect_account.account_id,
            name=user.full_name,
            email=user.email,
        )

        # Create the payment method in Stripe
        payment_method = stripe.PaymentMethod.create(
            type="customer_balance",
            stripe_account=connect_account.account_id,
        )

        init_args['stripe_account'] = connect_account.account_id
        init_args['payment_method_types'] = ["customer_balance"]
        init_args['payment_method'] = payment_method.id
        init_args['customer'] = customer.id
        init_args['confirm'] = True

        # Prepare Stripe and other necessary objects
        intent = stripe.PaymentIntent.create(
            **init_args
        )
        intent = serializer.save(
            intent_id=intent.id,
            client_secret=intent.client_secret,
            instructions=intent.next_action
        )
        donation.payment_intent = intent
        donation.save()
        StripePayment.objects.create(
            payment_intent=intent,
            donation=donation,
        )


class ConnectAccountList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = StripePayoutAccount.objects.all()
    serializer_class = ConnectAccountSerializer

    prefetch_for_includes = {
        'owner': ['owner'],
        'external_accounts': ['external_accounts'],
    }

    permission_classes = (IsAuthenticated, IsOwner,)

    def get_queryset(self, *args, **kwargs):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ConnectAccountDetails(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = StripePayoutAccount.objects.all()
    serializer_class = ConnectAccountSerializer

    permission_classes = (IsAuthenticated, IsOwner,)

    prefetch_for_includes = {
        "owner": ["owner"],
        "external_accounts": ["external_accounts"],
    }

    def perform_update(self, serializer):
        if (
                "country" in serializer.validated_data
                and serializer.instance.country != serializer.validated_data["country"]
        ):
            if serializer.instance.status == "verified":
                raise ValidationError("Cannot change country of verified account")

            serializer.instance.external_accounts.all().delete()
            serializer.instance.account_id = None
            serializer.instance.tos_acceptance = False

        return super().perform_update(serializer)


class ConnectAccountSession(JsonApiViewMixin, CreateAPIView):

    def create(self, request):
        stripe = get_stripe()
        account = get_object_or_404(
            StripePayoutAccount.objects.all(), pk=request.data.get("account_id")
        )
        if account.owner != request.user:
            raise PermissionDenied()

        # TODO check permissions on account
        account_session = stripe.AccountSession.create(
            account=account.account_id,
            components={
                "account_onboarding": {
                    "enabled": True,
                    "features": {"external_account_collection": False},
                },
                "account_management": {
                    "enabled": True,
                    "features": {"external_account_collection": False},
                },
            },
        )
        account_session.pk = account_session.client_secret
        serializer = self.get_serializer(instance=account_session)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    serializer_class = ConnectAccountSessionSerializer


class ConnectVerificationLink(JsonApiViewMixin, CreateAPIView):

    def create(self, request):
        stripe = get_stripe()
        account = get_object_or_404(
            StripePayoutAccount.objects.all(), pk=request.data.get("account_id")
        )
        if account.owner != request.user:
            raise PermissionDenied()

        # TODO check permissions on account

        verification_link = stripe.AccountLink.create(
            account=account.account_id,
            refresh_url=f'{get_current_host()}/activities/stripe/expired',
            return_url=f'{get_current_host()}/activities/stripe/complete',
            type="account_onboarding",
            collection_options={
                "fields": "eventually_due",
                "future_requirements": "include",
            }
        )

        verification_link.pk = str(uuid.uuid4())
        serializer = self.get_serializer(instance=verification_link)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    serializer_class = ConnectVerificationLinkSerializer


class ExternalAccountList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = ExternalAccount.objects.all()
    serializer_class = ExternalAccountSerializer

    prefetch_for_includes = {
        'connect_account': ['connect_account'],
    }

    related_permission_classes = {"connect_account": [IsOwner]}

    def get_queryset(self):
        settings = FundingPlatformSettings.objects.get()
        if settings.public_accounts:
            return self.queryset.order_by("-created").filter(
                connect_account__public=True,
                connect_account__status='verified'
            )
        else:
            return self.queryset.order_by("-created").filter(
                connect_account__owner=self.request.user
            )

    def perform_create(self, serializer):
        if hasattr(serializer.Meta, "model"):
            validated_data = dict(
                (key, value)
                for key, value in serializer.validated_data.items()
                if key != "token"
            )
            self.check_object_permissions(
                self.request, serializer.Meta.model(**validated_data)
            )
        serializer.save()


class ExternalAccountDetails(
    JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView
):
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
            if event.type == 'checkout.updated':
            q
            elif event.type == 'payment_intent.succeeded':
                payment = self.get_payment(event.data.object.id)
                if payment.status != payment.states.succeeded.value:
                    payment.states.succeed()
                    payment.update()
                    payment.donation.save()
                    payment.save()

                return HttpResponse('Updated payment to succeeded')

            elif event.type == 'payment_intent.payment_failed':
                payment = self.get_payment(event.data.object.id)
                if payment.status != payment.states.failed.value:
                    payment.states.fail(save=True)

                return HttpResponse('Updated payment to failed')

            elif event.type == 'charge.pending':
                if not event.data.object.payment_intent:
                    return HttpResponse('Not an intent payment')

                payment = self.get_payment(event.data.object.payment_intent)
                if payment.status != payment.states.pending.value:
                    payment.states.authorize(save=True)

                return HttpResponse('Updated payment to pending')

            elif event.type == 'charge.refunded':
                if not event.data.object.payment_intent:
                    return HttpResponse('Not an intent payment')

                payment = self.get_payment(event.data.object.payment_intent)
                payment.states.refund(save=True)

                return HttpResponse('Updated payment to refunded')
            else:
                return HttpResponse('Skipped event {}'.format(event.type))

        except StripePayment.DoesNotExist:
            return HttpResponse('Payment not found', status=400)

    def get_payment(self, payment_id):
        if PaymentIntent.objects.filter(id=payment_id).exists():
            intent = PaymentIntent.objects.get(intent_id=payment_id)
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


class SessionWebHookView(View):
    def post(self, request, **kwargs):
        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']
        stripe = get_stripe()

        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, stripe.webhook_secret_checkout
            )
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return HttpResponse('Signature failed to verify', status=400)

        if event.type.startswith('checkout.session'):
            session_id = event.data.object.id
            payment = GrantPayment.objects.filter(checkout_id=session_id).first()
            if payment:
                payment.check_status()


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
            error = "Signature failed to verify"
            logger.error(error)
            return HttpResponse(error, status=400)

        try:
            if event.type == "account.updated":
                account = self.get_account(event.data.object.id)

                external_account_ids = [
                    external_account.id for external_account
                    in event.data.object.external_accounts.data
                ]
                for bank_account in account.external_accounts.all():
                    if bank_account.account_id not in external_account_ids:
                        bank_account.delete()

                for external_account in event.data.object.external_accounts.data:
                    status = 'new'
                    if (
                        account.status == 'verified' and
                        external_account.requirements.currently_due == [] and
                        external_account.requirements.past_due == [] and
                        external_account.requirements.pending_verification == [] and
                        external_account.future_requirements.currently_due == [] and
                        external_account.future_requirements.past_due == [] and
                        external_account.future_requirements.pending_verification == []
                    ):
                        status = 'verified'
                    ExternalAccount.objects.get_or_create(
                        connect_account=account,
                        account_id=external_account.id,
                        defaults={'status': status}
                    )

                account.update(event.data.object)
                account.save()

                return HttpResponse("Updated connect account")
            else:
                return HttpResponse("Skipped event {}".format(event.type))

        except StripePayoutAccount.DoesNotExist:
            error = "Payout not found"
            logger.error(error)
            return HttpResponse(error, status=400)

    def get_account(self, account_id):
        return StripePayoutAccount.objects.get(account_id=account_id)


class CountrySpecList(JsonApiViewMixin, AutoPrefetchMixin, ListAPIView):
    serializer_class = CountrySpecSerializer

    def list(self, request, *args, **kwargs):
        stripe = get_stripe()
        specs = stripe.CountrySpec.list(limit=100)
        specs2 = stripe.CountrySpec.list(limit=100, starting_after=specs.data[-1].id)
        data = specs.data
        data.extend(specs2.data)
        serializer = self.get_serializer(data, many=True)

        for spec in data:
            spec.pk = spec.id

        return Response(serializer.data)


class CountrySpecDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveAPIView):
    serializer_class = CountrySpecSerializer

    def get_object(self):
        stripe = get_stripe()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )
        try:
            spec = stripe.CountrySpec.retrieve(self.kwargs[lookup_url_kwarg])
        except InvalidRequestError:
            raise Http404

        spec.pk = spec.id
        return spec
