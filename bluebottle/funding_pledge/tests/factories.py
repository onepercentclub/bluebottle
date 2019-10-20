import factory.fuzzy

from bluebottle.funding.tests.factories import DonationFactory
from bluebottle.funding_pledge.models import PledgePayment


class PledgePaymentFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = PledgePayment

    donation = factory.SubFactory(DonationFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        payment = super(PledgePaymentFactory, cls)._create(model_class, *args, **kwargs)
        payment.transitions.succeed()
        payment.save()
        return payment
