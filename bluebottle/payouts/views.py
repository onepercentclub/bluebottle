import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.funding_stripe.utils import stripe
from bluebottle.payouts.models import PayoutDocument
from bluebottle.payouts.models import StripePayoutAccount
from bluebottle.payouts.serializers import PayoutDocumentSerializer
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, RelatedResourceOwnerPermission, IsAuthenticated
)
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView, OwnerListViewMixin, PrivateFileView
)

logger = logging.getLogger(__name__)


class WebHookView(View):
    def post(self, request, **kwargs):
        payload = request.body
        signature_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, settings.STRIPE['webhook_secret_connect']
            )
            if event.type == 'account.updated':
                payout_account = StripePayoutAccount.objects.get(account_id=event.data.object.id)
                payout_account.check_status()
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return HttpResponse(status=400)
        except StripePayoutAccount.DoesNotExist:
            # StripePayoutAccount not found
            return HttpResponse(status=400)
        return HttpResponse(status=200)


class ManagePayoutDocumentPagination(BluebottlePagination):
    page_size = 20


class ManagePayoutDocumentList(OwnerListViewMixin, ListCreateAPIView):
    queryset = PayoutDocument.objects
    serializer_class = PayoutDocumentSerializer
    pagination_class = ManagePayoutDocumentPagination
    permission_classes = (IsAuthenticated, )
    owner_filter_field = 'author'

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user, ip_address=get_client_ip(self.request)
        )


class ManagePayoutDocumentDetail(RetrieveUpdateDestroyAPIView):
    queryset = PayoutDocument.objects
    serializer_class = PayoutDocumentSerializer
    pagination_class = ManagePayoutDocumentPagination

    permission_classes = (ResourcePermission, )

    def perform_update(self, serializer):
        serializer.save(
            author=self.request.user, ip_address=get_client_ip(self.request)
        )


class PayoutDocumentFileView(PrivateFileView):
    queryset = PayoutDocument.objects
    field = 'file'
    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
    )
