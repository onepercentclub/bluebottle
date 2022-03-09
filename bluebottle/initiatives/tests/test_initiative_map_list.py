from datetime import datetime, timezone, timedelta
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.urls import reverse


from bluebottle.test.utils import BluebottleTestCase
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.geo import GeolocationFactory


class InitiativeMapListTestCase(BluebottleTestCase):
    def setUp(self):

        cache.clear()
        self.url = reverse("initiative-map-list")

    def test_get_initiative_map_list_view(self):

        initiative_1 = InitiativeFactory(status="approved")
        initiative_2 = InitiativeFactory(status="approved")

        for initiative in [initiative_1, initiative_2]:
            initiative_url = reverse("initiative-detail", args=(initiative.id,))
            print(f"Running test for initiative {initiative.id}: {initiative.title}")
            response = self.client.get(initiative_url)

            self.assertEqual(response.data["id"], initiative.id)
            self.assertEqual(response.data["title"], initiative.title)

    def test_unapproved_initiatives_not_displayed(self):

        initiative_3 = InitiativeFactory(status="submitted")
        initiative_4 = InitiativeFactory(status="draft")
        initiative_5 = InitiativeFactory(status="sofmsljfalkdfjal;kj")
        unapproved_initiatives = [initiative_3, initiative_4, initiative_5]

        map_list_url = reverse("initiative-map-list")
        response = self.client.get(map_list_url)
        results_list = response.json()

        for initiative in unapproved_initiatives:
            title = initiative.title
            matching_initiatives = list(
                filter(lambda initiative: initiative["title"] == title, results_list)
            )
            self.assertNotIn(title, matching_initiatives)

    def test_initiatives_with_location(self):

        geolocation_1 = GeolocationFactory.create(
            position=Point(23.6851594, 43.0579025)
        )
        geolocation_2 = GeolocationFactory.create(position=Point(51.509865, -0.118092))
        initiative_1 = InitiativeFactory(status="approved", place=geolocation_1)
        initiative_2 = InitiativeFactory(status="approved", place=geolocation_2)

        response = self.client.get(self.url)
        results_list = response.json()

        for initiative in [initiative_1, initiative_2]:
            r = list(filter(lambda x: x["id"] == initiative.id, results_list))
            self.assertEqual(len(r), 1)

    def test_initiatives_with_zero_latlong(self):

        geolocation1 = GeolocationFactory.create(position=Point(0, 0))
        geolocation2 = GeolocationFactory.create(position=Point(0, 0))
        initiative1 = InitiativeFactory(status="approved", place=geolocation1)
        initiative2 = InitiativeFactory(status="approved", place=geolocation2)

        response = self.client.get(self.url)
        results_list = response.json()

        for initiative in [initiative1, initiative2]:
            r = list(filter(lambda x: x["id"] == initiative.id, results_list))
            self.assertEqual(len(r), 0)

    def test_cache_works(self):

        initiative_1 = InitiativeFactory(status="approved")
        initiative_2 = InitiativeFactory(status="approved")

        response = self.client.get(self.url)
        results_list = response.json()
        len_results_1 = len(results_list)

        initiative_3 = InitiativeFactory(status="approved")
        response = self.client.get(self.url)
        len_results_2 = len(response.json())

        self.assertEqual(len_results_1, len_results_2)

    def test_ordering_works(self):

        now = datetime.now()
        now = now.replace(tzinfo=timezone(timedelta(hours=1)))
        yesterday = now + timedelta(days=-1)
        yesterday_late = yesterday + timedelta(hours=10)

        initiative_1 = InitiativeFactory(status="approved")
        initiative_2 = InitiativeFactory(status="approved")
        initiative_3 = InitiativeFactory(status="approved")

        initiative_1.created = now
        initiative_1.save()

        initiative_2.created = yesterday
        initiative_2.save()

        initiative_3.created = yesterday_late
        initiative_3.save()

        initiative_list = [initiative_1, initiative_2, initiative_3]

        for initiative in initiative_list:
            initiative_url = reverse("initiative-detail", args=(initiative.id,))
            response = self.client.get(initiative_url)
            self.assertEqual(response.data["created"], initiative.created.isoformat())

        sorted_initiatives = sorted(initiative_list, key=lambda x: x.created)
        sorted_initiative_ids = [initiative.id for initiative in sorted_initiatives]

        response = self.client.get(self.url)
        initiative_ids = [initiative["id"] for initiative in response.json()]

        self.assertEqual(initiative_ids, sorted_initiative_ids)
