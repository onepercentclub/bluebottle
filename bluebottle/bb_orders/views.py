import logging
from bluebottle.bb_orders.models import OrderStatuses
from bluebottle.bb_orders.permissions import IsOrderCreator
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics
from django.utils.translation import ugettext as _
from .models import Order
from .serializers import OrderSerializer
from bluebottle.utils.utils import get_project_model

PROJECT_MODEL = get_project_model()

logger = logging.getLogger(__name__)


#
# Mixins.
#

anon_order_id_session_key = 'cart_order_id'

no_active_order_error_msg = _(u"No active order")


#
# REST views.
#

class OrderList(generics.ListCreateAPIView):
    model = Order
    serializer_class = OrderSerializer
    filter_fields = ('status',)
    paginate_by = 10
    # FIXME Add permissions

    def get_queryset(self):
        user = self.request.user
        return self.model.objects.filter(user=user)


class OrderDetail(generics.RetrieveUpdateAPIView):
    model = Order
    serializer_class = OrderSerializer
    permission_classes = (IsOrderCreator,)


