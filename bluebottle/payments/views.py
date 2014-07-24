from rest_framework import generics
from .serializers import PaymentMethodSerializer
from bluebottle.utils.utils import get_project_model

class PaymentMethodList(generics.ListAPIView):
    model = PaymentMethod
    serializer_class = PaymentMethodSerializer

    def get_queryset(self):
        queryset = super(PaymentMethodList, self).get_queryset()
        if self.request.user.is_authenticated():
            return queryset.filter(user=self.request.user)
        else:
            order_id = getattr(self.request.session, anonymous_order_id_session_key, 0)
            return queryset.filter(id=order_id)
