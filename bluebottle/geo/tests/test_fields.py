from django.contrib.gis.geos import Point

from bluebottle.geo.models import Geolocation
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.utils import BluebottleTestCase


class PointFieldTest(BluebottleTestCase):

    def test_geolocation_field(self):
        country = CountryFactory.create()
        geolocation = Geolocation.objects.create(
            position=Point(23.6764778, 43.0682267),
            mapbox_id='some-id',
            country=country
        )
        geolocation.save()
        self.assertEqual(geolocation.position.wkt, Point(23.6764778, 43.0682267).wkt)
