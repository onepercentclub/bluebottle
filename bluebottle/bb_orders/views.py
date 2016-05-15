import logging
from django.http import Http404
from bluebottle.bb_orders.permissions import IsOrderCreator, OrderIsNew
from bluebottle.bb_orders.signals import order_requested
from rest_framework import generics

from bluebottle.orders.models import Order
from bluebottle.orders.serializers import OrderSerializer, ManageOrderSerializer
from bluebottle.payments.services import PaymentService
from bluebottle.utils.utils import StatusDefinition

logger = logging.getLogger(__name__)

anonymous_order_id_session_key = 'new_order_id'


class OrderList(generics.ListCreateAPIView):
    model = Order
    serializer_class = OrderSerializer


class OrderDetail(generics.RetrieveUpdateAPIView):
    model = Order
    serializer_class = OrderSerializer


class ManageOrderList(generics.ListCreateAPIView):
    model = Order
    serializer_class = ManageOrderSerializer
    filter_fields = ('status',)
    paginate_by = 10

    def get_queryset(self):
        queryset = super(ManageOrderList, self).get_queryset()
        if self.request.user.is_authenticated():
            return queryset.filter(user=self.request.user)
        else:
            order_id = getattr(self.request.session,
                               anonymous_order_id_session_key, 0)
            return queryset.filter(id=order_id)

    def pre_save(self, obj):
        # If the user is authenticated then set that user to this order.
        if self.request.user.is_authenticated():
            obj.user = self.request.user

    def post_save(self, obj, created=False):
        # If the user isn't authenticated then save the order id in session/
        if created:
            self.request.session[anonymous_order_id_session_key] = obj.id
            self.request.session.save()


class ManageOrderDetail(generics.RetrieveUpdateAPIView):
    model = Order
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
        object = super(ManageOrderDetail, self).get_object(queryset)
        order_requested.send(sender=Order, order=object)
        return object
