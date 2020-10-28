import factory

from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from geoposition import Geoposition

from bluebottle.geo.models import (
    Country, SubRegion, Region, Location, LocationGroup, Place,
    Geolocation)


class RegionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Region

    name = factory.Sequence(lambda n: f'Region{n}')


class SubRegionFactory(factory.DjangoModelFactory):
    class Meta:
        model = SubRegion

    name = factory.Sequence(lambda n: f'SubRegion{n}')
    region = factory.SubFactory(RegionFactory)


class CountryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Country

    name = factory.Faker('country')
    subregion = factory.SubFactory(SubRegionFactory)


class LocationGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = LocationGroup

    name = factory.Sequence(lambda n: f'LocationGroup_{n}')


class LocationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f'Location_{n}')
    position = Geoposition(52.5, 13.4)
    country = factory.SubFactory(CountryFactory)
    group = factory.SubFactory(LocationGroupFactory)


class PlaceFactory(factory.DjangoModelFactory):
    class Meta:
        model = Place
        exclude = ['content_object']

    position = Geoposition(52.5, 13.4)
    country = factory.SubFactory(CountryFactory)

    object_id = factory.SelfAttribute('content_object.id')
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.content_object)
    )


class GeolocationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Geolocation

    street = factory.Faker('street_name')
    street_number = factory.Faker('building_number')
    locality = factory.Faker('city')
    position = Point(13.4, 52.5)
    country = factory.SubFactory(CountryFactory)
    formatted_address = factory.LazyAttribute(
        lambda o: '{} {} {} {}'.format(
            o.street, o.street_number, o.locality, o.country.name
        )
    )
