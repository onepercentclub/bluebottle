from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import TemplateView, View
from django.conf import settings

from bluebottle.payments.models import OrderPayment
from bluebottle.payments.services import PaymentService


class PaymentMock(TemplateView):
    """
    This view simulates an external Mock PSP server environment.
    """

    template_name = 'payments_mock/payment.html'

    def get(self, request, *args, **kwargs):
        # look for the callback key in the request and pass it back to the template

        order_payment_id = kwargs.get('order_payment_id', None)

        result = {'return_url': reverse('payment-service-provider-handler'),
                  'order_payment_id': order_payment_id}
        return render_to_response(self.template_name, result, RequestContext(request))


class PaymentResponseMockHandler(TemplateView):
    """
    This view is a Django handler for the return of the user from the mock PSP server. This view will handle
    the initial redirect from the server and redirect the user to the mock ember route that displays the
    page matching the user' chosen action.
    """

    payment_responses = ['success', 'cancelled', 'pending']

    def get(self, request, *args, **kwargs):
        status = request.GET.get('status')
        order_payment_id = request.GET.get('order_payment_id')

        order_payment = OrderPayment.objects.get(id=order_payment_id)

        # Set the order payment to authorized
        order_payment.authorized()
        order_payment.save()

        return_domain = getattr(settings, 'MOCK_PAYMENT_RETURN_DOMAIN', 'http://bluebottle.localhost:4200')
        if order_payment and status in self.payment_responses:
            url = "{0}/en/orders/{1}/{2}".format(return_domain, order_payment.order.id, status)

        else:
            raise Http404

        # # #Fake an external signal by calling our Payment Status Listener view and sending the chosen status.s
        # payload = {'order_payment_id': order_payment_id, 'status': status}
        # status_url = ''.join(['http://', get_current_site(request).domain,
        #                       reverse('payment-service-provider-status-update')])
        # import requests
        #
        # r = requests.post(status_url, data=payload)

        return HttpResponseRedirect(url)


class PaymentStatusListener(View):
    """
    This view simulates our listener that handles incoming messages from an external PSP to update the status of
    a payment. It's an "underwater" view and the user does not directly engage with this view or url, only the
    external server by making a POST request to it.
    """

    def post(self, request, *args, **kwargs):
        status = request.POST.get('status', None)
        order_payment_id = request.POST.get('order_payment_id')

        try:
            order_payment = OrderPayment.objects.get(id=order_payment_id)
        except OrderPayment.DoesNotExist:
            raise Http404

        service = PaymentService(order_payment)

        # We pass the MockPayment status and get back the status name of our OrderStatus definition
        service.adapter.set_order_payment_new_status(status)

        return HttpResponse('success')
