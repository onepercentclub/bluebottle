import json
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from bluebottle.bb_orders.permissions import IsOrderCreator, LoggedInUser
from bluebottle.payments.serializers import ManageOrderPaymentSerializer
from bluebottle.payments.services import get_payment_methods
from bluebottle.payments.models import Payment, OrderPayment
from bluebottle.payments.services import PaymentService


class PaymentMethodList(APIView):
    #serializer_class = OrderPaymentMethodSerializer
    permission_classes = (LoggedInUser,)

    def get(self, request, *args, **kw):
        # TODO: Determine country based on GET param, user settings or IP.
        country = 'NL'
        # TODO: Determine available methods based on country and GET params (amount).
        methods = get_payment_methods('NL', 500)

        result = {'country': country, 'results': methods}
        response = Response(result, status=status.HTTP_200_OK)
        return response


class PaymentMethodDetail(RetrieveAPIView):
    permission_classes = (LoggedInUser,)


class ManageOrderPaymentDetail(RetrieveUpdateAPIView):
    model = OrderPayment
    serializer_class = ManageOrderPaymentSerializer
    permission_classes = (IsOrderCreator,)

    def pre_save(self, obj):
        obj.amount = obj.order.total


class ManageOrderPaymentList(ListCreateAPIView):
    model = OrderPayment
    serializer_class = ManageOrderPaymentSerializer
    permission_classes = (IsOrderCreator,)

    def post_save(self, obj, created=False):
        service = PaymentService(obj)
        service.start_payment()

