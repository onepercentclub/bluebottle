from bluebottle.payments.adapters import get_payment_methods
from bluebottle.payments.models import Payment, PaymentMethod
from bluebottle.payments.serializers import ManagePaymentSerializer
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class PaymentMethodList(APIView):
    #serializer_class = PaymentMethodSerializer
    # FIXME: Permissions

    def get(self, request, *args, **kw):
        # TODO: Determine country based on GET param, user settings or IP.
        country = 'NL'
        # TODO: Determine available methods based on country and GET params (amount).
        methods = get_payment_methods('NL', 500)

        result = {'country': country, 'results': methods}
        response = Response(result, status=status.HTTP_200_OK)
        return response


class PaymentMethodDetail(RetrieveAPIView):

    model = PaymentMethod

    # FIXME: Permissions


class ManagePaymentDetail(RetrieveUpdateAPIView):
    model = Payment
    serializer_class = ManagePaymentSerializer
    # FIXME: Permissions

    def pre_save(self, obj):
        obj.amount = obj.order.total


class ManagePaymentList(ListCreateAPIView):
    model = Payment
    serializer_class = ManagePaymentSerializer
    # FIXME: Permissions

    def pre_save(self, obj):
        obj.amount = obj.order.total
