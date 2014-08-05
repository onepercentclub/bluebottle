from bluebottle.payments.adapters import get_payment_methods
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class PaymentMethodList(APIView):
    #serializer_class = PaymentMethodSerializer

    def get(self, request, *args, **kw):
        # TODO: Determine country based on GET param, user settings or IP.
        country = 'NL'
        # TODO: Determine available methods based on country and GET params (amount).
        methods = get_payment_methods('NL', 500)

        result = {'country': country, 'results': methods}
        response = Response(result, status=status.HTTP_200_OK)
        return response