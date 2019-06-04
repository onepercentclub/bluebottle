from bluebottle.funding.views import PaymentList
from bluebottle.funding_stripe.models import StripePayment
from bluebottle.funding_stripe.serializers import StripePaymentSerializer


class StripePaymentList(PaymentList):
    queryset = StripePayment.objects.all()
    serializer_class = StripePaymentSerializer
