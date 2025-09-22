import factory
from builtins import object

from bluebottle.activity_pub.models import (
    Organization, Inbox, Outbox, PublicKey, PrivateKey
)
from bluebottle.test.factory_models.organizations import OrganizationFactory as BluebottleOrganizationFactory


class PrivateKeyFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PrivateKey

    private_key_pem = factory.Faker('text')


class PublicKeyFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PublicKey

    public_key_pem = factory.Faker('text')
    private_key = factory.SubFactory(PrivateKeyFactory)


class InboxFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Inbox


class OutboxFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Outbox


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Organization

    name = factory.Sequence(lambda n: 'ActivityPub Organization {0}'.format(n))
    summary = factory.Faker('text', max_nb_chars=200)
    content = factory.Faker('text', max_nb_chars=500)
    image = factory.Faker('image_url')
    preferred_username = factory.Sequence(lambda n: 'activitypub_org_{0}'.format(n))

    inbox = factory.SubFactory(InboxFactory)
    outbox = factory.SubFactory(OutboxFactory)
    public_key = factory.SubFactory(PublicKeyFactory)
    organization = factory.SubFactory(BluebottleOrganizationFactory)
