from ipware.ip import get_ip

from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.generics import (RetrieveUpdateAPIView, ListCreateAPIView,
                                     RetrieveAPIView)
from rest_framework.response import Response
from rest_framework.views import APIView

from bluebottle.bb_orders.permissions import IsOrderCreator
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import OrderPayment
from bluebottle.payments.serializers import ManageOrderPaymentSerializer
from bluebottle.payments.services import get_payment_methods, PaymentService
from bluebottle.utils.utils import get_country_code_by_ip


class PaymentMethodList(APIView):
    def get(self, request, *args, **kwargs):
        if 'country' in request.GET:
            country = request.GET['country']
        else :
            ip = get_ip(request)
            if ip == '127.0.0.1':
                country = 'all'
            else:
                country = get_country_code_by_ip(ip)

        # Payment methods are loaded from the settings so they
        # aren't translated at run time. We need to do it manually
        from django.utils.translation import ugettext as _
        methods = get_payment_methods(country, 500)
        for method in methods:
            method['name'] = _(method['name'])

        result = {'country': country, 'results': methods}
        response = Response(result, status=status.HTTP_200_OK)
        return response


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
        """
        If there is an Order parameter in the GET request, filter
        the OrderPayments on the order
        """
        qs = OrderPayment.objects.all()
        order_id = self.request.QUERY_PARAMS.get('order', None)
        if order_id:
            qs = qs.filter(order__id=order_id)
        return qs
