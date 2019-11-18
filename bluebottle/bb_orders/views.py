import logging
from django.http import Http404
from bluebottle.bb_orders.permissions import IsOrderCreator, OrderIsNew
from bluebottle.utils import views


from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.orders.models import Order
from bluebottle.orders.serializers import ManageOrderSerializer
from bluebottle.payments.services import PaymentService
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.utils import StatusDefinition

logger = logging.getLogger(__name__)

anonymous_order_id_session_key = 'new_order_id'


class ManageOrderList(views.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = ManageOrderSerializer
    filter_fields = ('status',)
    pagination_class = BluebottlePagination
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        queryset = super(ManageOrderList, self).get_queryset()
        if self.request.user.is_authenticated():
            return queryset.filter(user=self.request.user)
        else:
            order_id = getattr(self.request.session,
                               anonymous_order_id_session_key, 0)
            return queryset.filter(id=order_id)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated():
            serializer.save(user=self.request.user)
        else:
            serializer.save()

            self.request.session[anonymous_order_id_session_key] = serializer.instance.id
            self.request.session.save()


class ManageOrderDetail(views.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = ManageOrderSerializer

    permission_classes = (IsOrderCreator, OrderIsNew)

    def get(self, request, *args, **kwargs):
        order = self.get_object()

        # Only check the status with the PSP if the order is locked or pending
        if order.status in [StatusDefinition.LOCKED, StatusDefinition.PENDING]:
            self.check_status_psp(order)
        return super(ManageOrderDetail, self).get(request, *args, **kwargs)

    def check_status_psp(self, order):
        try:
            order_payment = order.order_payments.all().order_by('-created')[0]
        except IndexError:
            raise Http404

        service = PaymentService(order_payment)
        service.adapter.check_payment_status()

    def get_object(self, queryset=None):
        object = super(ManageOrderDetail, self).get_object()
        return object
