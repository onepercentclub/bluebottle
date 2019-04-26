import factory

from bluebottle.organizations.models import OrganizationContact, Organization
from .accounts import BlueBottleUserFactory


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Organization

    name = factory.Sequence(lambda n: 'Organization_{0}'.format(n))
    slug = factory.Sequence(lambda n: 'organization_{0}'.format(n))
    description = 'Some info'
    website = 'https://goodup.com'
    owner = factory.SubFactory(BlueBottleUserFactory)


class OrganizationContactFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = OrganizationContact

    name = factory.Sequence(lambda n: 'Contact_{0}'.format(n))
    phone = factory.Sequence(lambda n: '555-{0}'.format(n))
    email = factory.Sequence(lambda n: '{0}@example.com'.format(n))
    owner = factory.SubFactory(BlueBottleUserFactory)
    organization = factory.SubFactory(OrganizationFactory)
