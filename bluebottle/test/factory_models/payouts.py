from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.utils.utils import StatusDefinition
from django.utils.timezone import now
import factory

from bluebottle.payouts.models import ProjectPayout


class ProjectPayoutFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ProjectPayout

    completed = None
    status = StatusDefinition.NEW
    planned = now()
    project = factory.SubFactory(ProjectFactory)
    amount_raised = 1000
    organization_fee = 50
    amount_payable = 950
