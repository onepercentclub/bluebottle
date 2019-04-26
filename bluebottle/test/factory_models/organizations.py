import factory

from bluebottle.organizations.models import OrganizationContact, Organization
from .geo import CountryFactory
from .accounts import BlueBottleUserFactory


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Organization

    name = factory.Sequence(lambda n: 'Organization_{0}'.format(n))
    slug = factory.Sequence(lambda n: 'organization_{0}'.format(n))
    address_line1 = "'s Gravenhekje 1a"
    address_line2 = '1011 TG'
    city = 'Amsterdam'
    state = 'North Holland'
    country = factory.SubFactory(CountryFactory, name='Netherlands')
    postal_code = '1011TG'

    # Contact
    phone_number = '(+31) 20 715 8980'
    website = 'http://onepercentclub.com'

    email = 'info@onepercentclub.com'


class OrganizationContactFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = OrganizationContact

    name = factory.Sequence(lambda n: 'Contact_{0}'.format(n))
    phone = factory.Sequence(lambda n: '555-{0}'.format(n))
    email = factory.Sequence(lambda n: '{0}@example.com'.format(n))
    owner = factory.SubFactory(BlueBottleUserFactory)
    organization = factory.SubFactory(OrganizationFactory)
