from django.views.generic import View
from django.http import HttpResponse, Http404

from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import CreateModelMixin
from rest_framework_json_api.views import AutoPrefetchMixin


from bluebottle.funding.views import PaymentList
from bluebottle.funding.transitions import PayoutAccountTransitions
from bluebottle.funding_stripe.utils import stripe
from bluebottle.funding_stripe.models import (
    StripePayment, StripePayoutAccount, ExternalAccount
)
from bluebottle.funding_stripe.serializers import (
    StripePaymentSerializer, ConnectAccountSerializer, ExternalAccountSerializer,
)
from bluebottle.members.models import Member
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, JsonApiViewMixin, CreateAPIView,
)


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
            obj = self.request.user.funding_stripe_payout_account
        except Member.funding_stripe_payout_account.RelatedObjectDoesNotExist:
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
            serializer.instance.update(token)
        serializer.save()


class ExternalAccountsList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    permission_classes = []

    queryset = ExternalAccount.objects.all()
    serializer_class = ExternalAccountSerializer

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
    serializer_class = ExternalAccountSerializer

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
        return StripePayment.objects.get(intent_id=intent_id)


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
