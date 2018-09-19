import factory
from bluebottle.votes.models import Vote
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class VoteFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Vote

    voter = factory.SubFactory(BlueBottleUserFactory)
    project = factory.SubFactory(ProjectFactory)
    ip_address = "127.0.0.1"

    @classmethod
    def create(cls, *args, **kwargs):
        created = kwargs.pop('created', None)
        obj = super(VoteFactory, cls).create(*args, **kwargs)
        if created is not None:
            obj.created = created
            obj.save()
        return obj
