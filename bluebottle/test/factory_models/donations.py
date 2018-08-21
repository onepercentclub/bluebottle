import factory
from moneyed import Money

from bluebottle.donations.models import Donation
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory


class DonationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Donation

    fundraiser = factory.SubFactory(FundraiserFactory)
    order = factory.SubFactory(OrderFactory)
    project = factory.SubFactory(ProjectFactory)
    reward = None
    amount = Money(25, 'EUR')

    @classmethod
    def create(cls, *args, **kwargs):
        created = kwargs.pop('created', None)
        obj = super(DonationFactory, cls).create(*args, **kwargs)
        if created is not None:
            obj.created = created
            obj.save()
        return obj
