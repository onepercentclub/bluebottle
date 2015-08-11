import factory
from bluebottle.votes.models import Vote
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class VoteFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Vote

    voter = factory.SubFactory(BlueBottleUserFactory)
    project = factory.SubFactory(ProjectFactory)
