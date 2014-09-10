import json
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.serializers import ManageOrderPaymentSerializer
from bluebottle.payments.services import get_payment_methods
from bluebottle.payments.models import Payment, OrderPayment
from bluebottle.payments.services import PaymentService
from rest_framework.exceptions import APIException, ParseError
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class PaymentMethodList(APIView):
    #serializer_class = OrderPaymentMethodSerializer
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
    # FIXME: Permissions
    pass


class ManageOrderPaymentDetail(RetrieveUpdateAPIView):
    model = OrderPayment
    serializer_class = ManageOrderPaymentSerializer
    # FIXME: Permissions

    def pre_save(self, obj):
        obj.amount = obj.order.total


class ManageOrderPaymentList(ListCreateAPIView):
    model = OrderPayment
    serializer_class = ManageOrderPaymentSerializer
    # FIXME: Permissions

    def post_save(self, obj, created=False):
        try:
            service = PaymentService(obj)
            service.start_payment()
        except PaymentException as error:
            raise ParseError(detail=str(error))

