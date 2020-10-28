import factory

from bluebottle.organizations.models import OrganizationContact, Organization
from .accounts import BlueBottleUserFactory


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f'Organization_{n}')
    slug = factory.Sequence(lambda n: f'organization_{n}')
    description = 'Some info'
    website = 'https://goodup.com'
    owner = factory.SubFactory(BlueBottleUserFactory)


class OrganizationContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = OrganizationContact

    name = factory.Sequence(lambda n: f'Contact_{n}')
    phone = factory.Sequence(lambda n: f'555-{n}')
    email = factory.Sequence(lambda n: f'{n}@example.com')
    owner = factory.SubFactory(BlueBottleUserFactory)
