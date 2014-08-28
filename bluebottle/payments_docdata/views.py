from django.http import HttpResponse
from django.views.generic import View

from bluebottle.payments_docdata.models import DocdataPayment


class UpdatePaymentMixin(object):
    """
    Base mixin for updating the order from the API or return URL.
    """

    # What docdata calls the order_id, we call the payment_cluster_key
    # Docdata uses both the payment_cluster_id and merchant_order_id in the requests, depending on the view.
    payment_query_arg = 'order_id'
    payment_slug_field = 'payment_cluster_id'
    facade_class = Facade

    def get_order_slug(self):
        try:
            return self.request.GET[self.payment_query_arg]
        except KeyError:
            raise KeyError("Missing {0} parameter".format(self.payment_query_arg))

    def get_payment(self, payment_slug):
        """
        Update the status of an order, by fetching the latest state from docdata.
        """
        try:
            return DocdataPayment.objects.select_for_update().get(**{self.payment_slug_field: payment_slug})
        except DocdataPayment.DoesNotExist:
            logger.error("Order {0}='{1}' not found to update payment status.".format(self.payment_slug_field, payment_slug))
            raise Http404(u"Order {0}='{1}' not found!".format(self.payment_slug_field, payment_slug))

    def update_payment(self):
        self.payment # DocdataPayment
        adapter = DocdataPaymentAdapter(order_payment=self.payment.order_payment)


class PaymentStatusUpdateView(View, UpdatePaymentMixin):
    payment_slug_field = 'merchant_order_id'

    def get(self, request, *args, **kwargs):
        try:
            payment_key = self.get_payment_slug()
        except KeyError as e:
            return HttpResponseBadRequest(e.message, content_type='text/plain; charset=utf-8')

        with transaction_atomic():
            try:
                self.payment = self.get_payment(payment_key)
            except Http404 as e:
                return HttpResponseNotFound(str(e), content_type='text/plain; charset=utf-8')

            try:
                self.update_payment(self.payment)
            except DocdataStatusError as e:
                logger.exception("The payment status could not be retrieved from Docdata by the notification URL")
                return HttpResponseServerError(
                    "Failed to fetch status from Docdata API.\n"
                    "\n\n"
                    "Docdata API response:\n"
                    "---------------------\n"
                    "\n"
                    "code:    {0}\n"
                    "message: {1}".format(e.code, e.message),
                    content_type='text/plain; charset=utf-8'
                )

        signal_kwargs = {
            'sender': self.payment.__class__,
            'instance': self.payment
        }
        responses = payment_status_changed.send(**signal_kwargs)

        # Return 200 as required by DocData when the status changed notification was consumed.
        return HttpResponse(u"Ok, payment updated", content_type='text/plain; charset=utf-8')
