from ipware.ip import get_ip

from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings
from django.utils.translation import ugettext as _
from bluebottle.orders.permissions import IsOrderCreator
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import OrderPayment
from bluebottle.payments.permissions import CanAccessPaymentMethod
from bluebottle.payments.serializers import ManageOrderPaymentSerializer
from bluebottle.payments.services import get_payment_methods, PaymentService
from bluebottle.utils.utils import get_country_code_by_ip


class PaymentMethodList(APIView):
    def get(self, request, *args, **kwargs):
        country = request.GET.get('country')

        if not country and not getattr(settings, 'SKIP_IP_LOOKUP', False):
            ip = get_ip(request)
            country = get_country_code_by_ip(ip)

        # Payment methods are loaded from the settings so they
        # aren't translated at run time. We need to do it manually
        methods = get_payment_methods(
            country=country,
            user=request.user,
            currency=request.GET.get('currency'),
            project_id=request.GET.get('project_id')
        )

        for method in methods:
            method['name'] = _(method['name'])

        result = {'country': country, 'results': methods}
        response = Response(result, status=status.HTTP_200_OK)
        return response


class PayoutAccountPaymentMethodList(APIView):
    def get(self, pk, request, *args, **kwargs):
        country = request.GET.get('country')

        if not country and not getattr(settings, 'SKIP_IP_LOOKUP', False):
            ip = get_ip(request)
            country = get_country_code_by_ip(ip)

        # Payment methods are loaded from the settings so they
        # aren't translated at run time. We need to do it manually
        methods = get_payment_methods(
            country=country, user=request.user, currency=request.GET.get('currency')
        )

        for method in methods:
            method['name'] = _(method['name'])

        result = {'country': country, 'results': methods}
        response = Response(result, status=status.HTTP_200_OK)
        return response


class ManageOrderPaymentDetail(RetrieveUpdateAPIView):
    queryset = OrderPayment.objects.all()
    serializer_class = ManageOrderPaymentSerializer
    permission_classes = (IsOrderCreator,)

    def perform_update(self, serializer):
        serializer.save(amount=serializer.validated_data['order'].total)
        # store integration_data in non-persisted card_data field
        serializer.instance.card_data = serializer.validated_data['integration_data']
        service = PaymentService(serializer.instance)
        try:
            service.check_payment_status()
        except PaymentException as error:
            raise ParseError(detail=unicode(error))


class ManageOrderPaymentList(ListCreateAPIView):
    queryset = OrderPayment.objects.all()
    serializer_class = ManageOrderPaymentSerializer
    permission_classes = (IsOrderCreator, CanAccessPaymentMethod)

    def perform_create(self, serializer):
        if self.request.user and self.request.user.is_authenticated():

            serializer.save(user=self.request.user)

            if not serializer.instance.order.user:
                serializer.instance.order.user = self.request.user
                serializer.instance.order.save()
        else:
            serializer.save()

        try:
            service = PaymentService(serializer.instance)
            service.start_payment()
        except PaymentException as error:
            raise ParseError(detail=unicode(error))

    def get_queryset(self):
        """
        If there is an Order parameter in the GET request, filter
        the OrderPayments on the order
        """
        qs = OrderPayment.objects.all()
        order_id = self.request.query_params.get('order', None)
        if order_id:
            qs = qs.filter(order__id=order_id)
        return qs
