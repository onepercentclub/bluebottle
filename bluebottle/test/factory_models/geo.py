import factory
from random import randint
from bluebottle.utils.model_dispatcher import get_project_model
from bluebottle.geo.models import Country, SubRegion, Region, Location
from geoposition import Geoposition


PROJECT_MODEL = get_project_model()


class RegionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Region

    name = factory.Sequence(lambda n: 'Region{0}'.format(n))


class SubRegionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = SubRegion

    name = factory.Sequence(lambda n: 'SubRegion{0}'.format(n))
    region = factory.SubFactory(RegionFactory)


class CountryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Country

    name = factory.Sequence(lambda n: 'Country_{0}'.format(n))
    subregion = factory.SubFactory(SubRegionFactory)


class LocationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Location

    name = factory.Sequence(lambda n: 'Location_{0}'.format(n))
    position = Geoposition(52.5, 13.4)
