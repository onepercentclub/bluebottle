# -*- coding: utf-8 -*-
import httmock
import json
import urlparse

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase
from django.core.management import call_command
from django.test.utils import override_settings

mock_result = {
    'results': [
        {
            "address_components": [
                {
                    "long_name": "36",
                    "short_name": "36",
                    "types": ["street_number"]
                },
                {
                    "long_name": "161",
                    "short_name": "161",
                    "types": ["route"]
                },
                {
                    "long_name": "Lyutidol",
                    "short_name": "Lyutidol",
                    "types": ["locality", "political"]
                },
                {
                    "long_name": "Vratza",
                    "short_name": "Vratza",
                    "types": ["administrative_area_level_1", "political"]
                },
                {
                    "long_name": "Bulgaria",
                    "short_name": "BG",
                    "types": ["country", "political"]
                },
                {
                    "long_name": "3165",
                    "short_name": "3165",
                    "types": ["postal_code"]
                }
            ],
            "formatted_address": "161 36, 3165 Lyutidol, Bulgaria",
            "geometry": {
                "location": {
                    "lat": 43.0647349,
                    "lng": 23.6758961
                },
                "location_type": "ROOFTOP",
                "viewport": {
                    "northeast": {
                        "lat": 43.06608388029149,
                        "lng": 23.6772450802915
                    },
                    "southwest": {
                        "lat": 43.06338591970849,
                        "lng": 23.6745471197085
                    }
                }
            },
            "place_id": "ChIJG7ZGBpj9qkAR3i3xGROaFO8",
            "types": ["street_address"]
        }],
    'status': 'OK'
}


class TestReverseGeocodeCommand(BluebottleTestCase):

    def setUp(self):
        super(TestReverseGeocodeCommand, self).setUp()
        self.init_projects()
        self.project = ProjectFactory.create(
            latitude=43.068620,
            longitude=23.676374
        )
        self.command = 'reverse_geocode_projects'

    @property
    def geocode_mock_factory(self):
        @httmock.urlmatch(netloc='maps.googleapis.com')
        def geocode_mock(url, request):
            self.assertEqual(
                urlparse.parse_qs(url.query)['language'][0], self.project.language.code
            )
            return json.dumps(mock_result)

        return geocode_mock

    @override_settings(MAPS_API_KEY='Bla123Bla')
    def test_run_command(self):
        with httmock.HTTMock(self.geocode_mock_factory):
            call_command(self.command)
        self.assertEquals(self.project.projectlocation.city, 'Lyutidol')
        self.assertEquals(self.project.projectlocation.country, 'Bulgaria')
