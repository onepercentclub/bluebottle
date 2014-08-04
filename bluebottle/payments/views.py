from bluebottle.payments.adapters import get_payment_methods
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import PaymentMethodSerializer


class PaymentMethodList(APIView):
    serializer_class = PaymentMethodSerializer

    def get(self, request, *args, **kw):
        result = get_payment_methods('NL', 500)
        response = Response(result, status=status.HTTP_200_OK)
        return response