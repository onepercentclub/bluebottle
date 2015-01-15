from bluebottle.projects.models import PartnerOrganization
import factory


class PartnerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PartnerOrganization
    FACTORY_DJANGO_GET_OR_CREATE = ('name', )

    name = factory.Sequence(lambda n: 'Partner_{0}'.format(n))
