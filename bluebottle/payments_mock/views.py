from django.views.generic import TemplateView
from django.shortcuts import render_to_response
from django.template import RequestContext


class PaymentMock(TemplateView):

    template_name = 'payments_mock/payment.html'

    def get(self, request, *args, **kwargs):
        # look for the callback key in the request and pass it back to the template

        callback = request.GET.get('callback')
        result = {'callback': callback}
        return render_to_response(self.template_name, result, context_instance=RequestContext(request))
