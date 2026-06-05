from builtins import object

import factory
from django.contrib.gis.geos import Point

from bluebottle.geo.models import (
    Country, SubRegion, Region, Location, LocationGroup, Place,
    Geolocation)


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
        django_get_or_create = ("alpha2_code",)

    name = factory.Faker('country')
    alpha2_code = factory.Faker('country_code')
    subregion = factory.SubFactory(SubRegionFactory)


class LocationGroupFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = LocationGroup

    name = factory.Sequence(lambda n: 'LocationGroup_{0}'.format(n))


class LocationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Location

    name = factory.Sequence(lambda n: 'Location_{0}'.format(n))
    position = Point(52.5, 13.4)
    country = factory.SubFactory(CountryFactory)
    group = factory.SubFactory(LocationGroupFactory)


class PlaceFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Place
        exclude = ['content_object']

    position = Point(52.5, 13.4)
    country = factory.SubFactory(CountryFactory)


class GeolocationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Geolocation

    street = factory.Faker('street_name')
    street_number = factory.Faker('building_number')
    locality = factory.Faker('city')
    position = Point(13.4, 52.5)
    country = factory.SubFactory(CountryFactory)
    mapbox_id = None
    formatted_address = factory.LazyAttribute(
        lambda o: '{} {} {} {}'.format(
            o.street, o.street_number, o.locality, o.country.name if o.country else ''
        )
    )

    @factory.post_generation
    def geofeatures(self, create, extracted, **kwargs):
        if not create or extracted is False:
            return

        from bluebottle.geo.models import GeoFeature
        from bluebottle.utils.models import Language

        languages = list(Language.objects.values_list('code', flat=True)) or ['en']

        place_feature, _ = GeoFeature.objects.get_or_create(
            mapbox_id=f'test-place-{self.pk}',
            defaults={'place_type': 'place'},
        )
        for code in languages:
            place_feature.set_current_language(code)
            place_feature.name = self.locality or ''
            place_feature.save()

        feature_ids = [place_feature.pk]
        if self.country_id:
            country_feature, _ = GeoFeature.objects.get_or_create(
                mapbox_id=f'test-country-{self.country.alpha2_code}',
                defaults={
                    'place_type': 'country',
                    'code': self.country.alpha2_code,
                },
            )
            for code in languages:
                country_feature.set_current_language(code)
                country_feature.name = self.country.name
                country_feature.save()
            feature_ids.append(country_feature.pk)

        self.features.set(feature_ids)
