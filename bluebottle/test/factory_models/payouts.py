import factory

from bluebottle.payouts.models import ProjectPayout


class ProjectPayoutFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ProjectPayout

    completed = None
    status = None
