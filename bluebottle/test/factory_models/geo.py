import factory
from bluebottle.geo.models import (
    Country, SubRegion, Region, Location, LocationGroup, Place
)
from geoposition import Geoposition


class RegionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Region

    name = factory.Sequence(lambda n: 'Region{0}'.format(n))


class SubRegionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = SubRegion

    name = factory.Sequence(lambda n: 'SubRegion{0}'.format(n))
    region = factory.SubFactory(RegionFactory)


class CountryFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Country

    name = factory.Sequence(lambda n: 'Country_{0}'.format(n))
    subregion = factory.SubFactory(SubRegionFactory)


class LocationGroupFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LocationGroup

    name = factory.Sequence(lambda n: 'LocationGroup_{0}'.format(n))


class LocationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Location

    name = factory.Sequence(lambda n: 'Location_{0}'.format(n))
    position = Geoposition(52.5, 13.4)
    country = factory.SubFactory(CountryFactory)
    group = factory.SubFactory(LocationGroupFactory)


class PlaceFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Place

    position = Geoposition(52.5, 13.4)
    country = factory.SubFactory(CountryFactory)
