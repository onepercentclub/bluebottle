import logging
from bluebottle.bb_orders.permissions import IsOrderCreator
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics
from bluebottle.utils.utils import get_project_model, get_model_class, get_serializer_class


ORDER_MODEL = get_model_class('ORDERS_ORDER_MODEL')
PROJECT_MODEL = get_project_model()

logger = logging.getLogger(__name__)

anonymous_order_id_session_key = 'cart_order_id'


class OrderList(generics.ListCreateAPIView):
    model = ORDER_MODEL
    serializer_class = get_serializer_class('ORDERS_ORDER_MODEL', 'preview')


class OrderDetail(generics.RetrieveUpdateAPIView):
    model = ORDER_MODEL
    serializer_class = get_serializer_class('ORDERS_ORDER_MODEL', 'preview')


class ManageOrderList(generics.ListCreateAPIView):
    model = ORDER_MODEL
    serializer_class = get_serializer_class('ORDERS_ORDER_MODEL', 'manage')
    filter_fields = ('status',)
    paginate_by = 10
    permission_classes = (IsOrderCreator, )

    def get_queryset(self):
        queryset = super(ManageOrderList, self).get_queryset()
        if self.request.user.is_authenticated():
            return queryset.filter(user=self.request.user)
        else:
            order_id = getattr(self.request.session, anonymous_order_id_session_key, 0)
            import ipdb; ipdb.set_trace()
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
    model = ORDER_MODEL
    serializer_class = get_serializer_class('ORDERS_ORDER_MODEL', 'manage')
    permission_classes = (IsOrderCreator,)

