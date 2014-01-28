import factory

from bluebottle.organizations import get_organization_model
from bluebottle.organizations.models import OrganizationMember
from bluebottle.test.factory_models.geo_factories import CountryFactory
from bluebottle.test.factory_models.accounts_factories import BlueBottleUserFactory

ORGANIZATION_MODEL = get_organization_model()


class OrganizationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ORGANIZATION_MODEL

    name = factory.Sequence(lambda n: 'Organization_{0}'.format(n))
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
    twitter = '@1percentclub'
    facebook = '/onepercentclub'
    skype = 'onepercentclub'


class OrganizationMemberFactory(factory.DjangoModelFactory):
    FACTORY_FOR = OrganizationMember

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
    function = 'owner'
