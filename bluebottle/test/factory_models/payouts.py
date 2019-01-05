from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.utils.utils import StatusDefinition
from django.utils.timezone import now
import factory

from bluebottle.payouts.models import (
    ProjectPayout, PayoutAccount, PlainPayoutAccount,
    PayoutDocument, StripePayoutAccount
)


class PayoutAccountFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(BlueBottleUserFactory)

    class Meta(object):
        model = PayoutAccount


class PlainPayoutAccountFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(BlueBottleUserFactory)

    class Meta(object):
        model = PlainPayoutAccount


class PayoutDocumentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PayoutDocument


class StripePayoutAccountFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(BlueBottleUserFactory)
    account_id = factory.Sequence(lambda n: 'acct_0000000{0}'.format(n))

    class Meta(object):
        model = StripePayoutAccount


class ProjectPayoutFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ProjectPayout

    completed = None
    status = StatusDefinition.NEW
    planned = now()
    project = factory.SubFactory(ProjectFactory)
    amount_raised = 1000
    organization_fee = 50
    amount_payable = 950
