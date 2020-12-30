import factory
from geoposition import Geoposition

from bluebottle.geo.models import Location
from bluebottle.offices.models import OfficeRegion, OfficeSubRegion
from bluebottle.test.factory_models.geo import CountryFactory


class OfficeRegionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = OfficeRegion

    name = factory.Sequence(lambda n: 'Region{0}'.format(n))


class OfficeSubRegionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = OfficeSubRegion

    name = factory.Sequence(lambda n: 'SubRegion{0}'.format(n))
    region = factory.SubFactory(OfficeRegionFactory)


class LocationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Location

    name = factory.Sequence(lambda n: 'Location_{0}'.format(n))
    position = Geoposition(52.5, 13.4)
    country = factory.SubFactory(CountryFactory)
