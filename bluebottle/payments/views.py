import json
from ipware.ip import get_ip
from rest_framework.exceptions import APIException, ParseError
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.serializers import ManageOrderPaymentSerializer
from bluebottle.payments.services import get_payment_methods
from bluebottle.payments.models import Payment, OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.bb_orders.permissions import IsOrderCreator, LoggedInUser
from bluebottle.payments.serializers import ManageOrderPaymentSerializer
from bluebottle.payments.services import get_payment_methods
from bluebottle.payments.models import Payment, OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.utils.utils import get_country_by_ip

class PaymentMethodList(APIView):
    #serializer_class = OrderPaymentMethodSerializer
    permission_classes = (LoggedInUser,)

    def get(self, request, *args, **kwargs):
        ip = get_ip(request)
        if ip == '127.0.0.1':
            country = 'all' #get_payment_methods returns all methods when 'all' is specified
        else:
            country = get_country_by_ip(ip)

        # TODO: Determine available methods based on GET params (amount).
        methods = get_payment_methods(country, 500)

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
        try:
            service = PaymentService(obj)
            service.start_payment()
        except PaymentException as error:
            raise ParseError(detail=str(error))

