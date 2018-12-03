from bluebottle.payouts.models.plain import PayoutDocument
from bluebottle.payouts.serializers.plain import PayoutDocumentSerializer
from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.views import ListCreateAPIView, RetrieveUpdateDestroyAPIView, OwnerListViewMixin, PrivateFileView
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, RelatedResourceOwnerPermission,
)


class ManagePayoutDocumentPagination(BluebottlePagination):
    page_size = 20


class ManagePayoutDocumentList(OwnerListViewMixin, ListCreateAPIView):
    queryset = PayoutDocument.objects
    serializer_class = PayoutDocumentSerializer
    pagination_class = ManagePayoutDocumentPagination
    filter = ('payout_account', )
    permission_classes = (ResourcePermission, )

    owner_filter_field = 'project__owner'

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        serializer.save(
            author=self.request.user, ip_address=get_client_ip(self.request)
        )


class ManagePayoutDocumentDetail(RetrieveUpdateDestroyAPIView):
    queryset = PayoutDocument.objects
    serializer_class = PayoutDocumentSerializer
    pagination_class = ManagePayoutDocumentPagination
    filter = ('payout_account', )

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
