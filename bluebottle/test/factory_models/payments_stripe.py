import factory

from bluebottle.payments_stripe.models import StripePayment
from bluebottle.test.factory_models.payments import OrderPaymentFactory


class StripePaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = StripePayment

    order_payment = factory.SubFactory(OrderPaymentFactory)
