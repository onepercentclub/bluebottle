from bluebottle.payouts.models import PayoutDocument
from bluebottle.payouts.serializers import PayoutDocumentSerializer
from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.views import ListCreateAPIView, RetrieveUpdateDestroyAPIView, OwnerListViewMixin, PrivateFileView
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, RelatedResourceOwnerPermission, IsAuthenticated)


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
