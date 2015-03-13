import json

from bluebottle.bb_orders.permissions import IsOrderCreator, LoggedInUser
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import OrderPayment, Payment
from bluebottle.payments.serializers import ManageOrderPaymentSerializer
from bluebottle.payments.services import PaymentService, get_payment_methods
from bluebottle.utils.utils import get_country_by_ip
from rest_framework import status
from rest_framework.exceptions import APIException, ParseError
from rest_framework.generics import (ListCreateAPIView, RetrieveAPIView,
                                     RetrieveUpdateAPIView)
from rest_framework.response import Response
from rest_framework.views import APIView

from ipware.ip import get_ip


class PaymentMethodList(APIView):

    def get(self, request, *args, **kwargs):
        ip = get_ip(request)
        if ip == '127.0.0.1':
            country = 'all' #get_payment_methods returns all methods when 'all' is specified
        else:
            country = get_country_by_ip(ip)

        # TODO: 1) Determine available methods based on GET params (amount).
        #       2) Re-enable country-based filtering when front-end can handle
        #          manually setting the country. For now send all methods.
        methods = get_payment_methods('all', 500)

        result = {'country': country, 'results': methods}
        response = Response(result, status=status.HTTP_200_OK)
        return response


class PaymentMethodDetail(RetrieveAPIView):
    pass


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

    def pre_save(self, obj):
        if self.request.user and self.request.user.is_authenticated():
            obj.user = self.request.user

    def post_save(self, obj, created=False):
        try:
            service = PaymentService(obj)
            service.start_payment()
        except PaymentException as error:
            print error
            raise ParseError(detail=str(error))
    
    def get_queryset(self):
        """ If there is an Order parameter in the GET request, filter the OrderPayments on the order """
        qs = OrderPayment.objects.all()
        order_id = self.request.QUERY_PARAMS.get('order', None)
        if order_id:
            qs = qs.filter(order__id=order_id)
        return qs
