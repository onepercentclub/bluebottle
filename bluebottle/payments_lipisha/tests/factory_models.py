import factory
from moneyed.classes import Money, KES

from bluebottle.payments_lipisha.models import LipishaProject
from bluebottle.test.factory_models.payments import OrderPaymentFactory, OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory

from ..models import LipishaPayment


class LipishaOrderFactory(OrderFactory):
    total = Money(250, KES)


class LipishaOrderPaymentFactory(OrderPaymentFactory):
    payment_method = 'telesomZaad'
    order = factory.SubFactory(LipishaOrderFactory)
    amount = Money(250, KES)


class LipishaPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LipishaPayment
    order_payment = factory.SubFactory(LipishaOrderPaymentFactory)


class LipishaProjectFactory(factory.DjangoModelFactory):
    project = factory.SubFactory(ProjectFactory)
    account_number = factory.Sequence(lambda n: '{0}'.format(n + 171234))

    class Meta:
        model = LipishaProject
