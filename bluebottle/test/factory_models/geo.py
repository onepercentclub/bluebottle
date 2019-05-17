import factory

from django.contrib.contenttypes.models import ContentType
from geoposition import Geoposition

from bluebottle.geo.models import (
    Country, SubRegion, Region, Location, LocationGroup, Place,
    InitiativePlace
)


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
        exclude = ['content_object']

    position = Geoposition(52.5, 13.4)
    country = factory.SubFactory(CountryFactory)

    object_id = factory.SelfAttribute('content_object.id')
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.content_object)
    )


class InitiativePlaceFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = InitiativePlace

    position = Geoposition(52.5, 13.4)
    country = factory.SubFactory(CountryFactory)
