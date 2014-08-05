from rest_framework.views import APIView
from django.shortcuts import render_to_response
from django.template import RequestContext

class PaymentMock(APIView):

    def get(self, request, *args, **kwargs):
        callback = request.GET.get('callback')

        result = {'callback': callback}
        return render_to_response('templates/payments_mock/payment.html', result, context_instance=RequestContext(request))
