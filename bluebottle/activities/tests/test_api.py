import datetime
import json
import re
from builtins import str
from datetime import timedelta

import dateutil
from django.contrib.gis.geos import Point
from django.test import tag
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now
from django_elasticsearch_dsl.test import ESTestCase
from pytz import UTC
from rest_framework import status

from bluebottle.activities.models import Activity
from bluebottle.collect.tests.factories import (
    CollectActivityFactory,
    CollectContributorFactory,
)
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.funding.tests.factories import DonorFactory, FundingFactory
from bluebottle.initiatives.models import (
    ActivitySearchFilter,
    InitiativePlatformSettings,
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.offices.tests.factories import OfficeSubRegionFactory
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.categories import CategoryFactory
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.factory_models.geo import (
    CountryFactory,
    GeolocationFactory,
    LocationFactory,
    PlaceFactory,
)
from bluebottle.test.utils import APITestCase, BluebottleTestCase, JSONAPITestClient
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    SkillFactory,
    DateRegistrationFactory,
)


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class ActivityListSearchAPITestCase(ESTestCase, BluebottleTestCase):
    def setUp(self):
        super(ActivityListSearchAPITestCase, self).setUp()

        self.client = JSONAPITestClient()
        self.url = reverse('activity-preview-list')
        self.owner = BlueBottleUserFactory.create()

    def search(self, filter, sort=None, user=None, place=None, headers=None):
        if isinstance(filter, str):
            url = filter
        else:
            params = dict(
                (f'filter[{key}]', value) for key, value in filter.items()
            )

            if sort:
                params['sort'] = sort

            if place:
                params['place'] = place

            query = '&'.join(f'{key}={value}' for key, value in params.items())

            url = f'{self.url}?{query}'

        if headers is None:
            headers = {}

        response = self.client.get(
            url,
            user=user,
            **headers
        )

        self.data = json.loads(response.content)

    def assertFound(self, matching, count=None):
        self.assertEqual(self.data['meta']['pagination']['count'], len(matching))

        if count:
            self.assertEqual(len(self.data['data']), count)

        ids = set(str(activity.pk) for activity in matching)

        for activity in self.data['data']:
            self.assertTrue(activity['id'] in ids)

    def assertFacets(self, filter, facets):
        counts = dict(
            (facet['id'], facet['count']) for facet in self.data['meta']['facets'][filter]
        )
        names = dict(
            (facet['id'], facet.get('name')) for facet in self.data['meta']['facets'][filter]
        )

        for key, (name, value) in facets.items():
            self.assertEqual(counts[key], value)
            self.assertEqual(names[key], name)

    def test_images(self):
        DateActivityFactory.create(
            owner=self.owner, status='open', image=ImageFactory.create()
        )
        DeadlineActivityFactory.create(status='open', image=ImageFactory.create())
        FundingFactory.create(review_status='open', image=ImageFactory.create())

        response = self.client.get(self.url, user=self.owner)

        for activity in response.json()['data']:
            self.assertTrue(
                re.match('^/api/activities/\d+/image/600x337', activity['attributes']['image'])
            )

    def test_deed_preview(self):
        activity = DeedFactory.create(status='open')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], True)
        self.assertEqual(attributes['is-full'], None)
        self.assertEqual(attributes['theme'], activity.theme.name)

    def test_date_preview(self):
        activity = DateActivityFactory.create(status='open')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(attributes['is-full'], False)
        self.assertEqual(attributes['theme'], activity.theme.name)
        self.assertEqual(attributes['expertise'], activity.expertise.name)
        self.assertEqual(attributes['slot-count'], 1)
        self.assertEqual(dateutil.parser.parse(attributes['start']), activity.slots.first().start)
        self.assertEqual(dateutil.parser.parse(attributes['end']), activity.slots.first().end)
        self.assertEqual(attributes['has-multiple-locations'], False)
        location = activity.slots.first().location
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_date_preview_multiple_slots(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create_batch(3, activity=activity)
        DateActivitySlotFactory.create(
            status='succeeded', activity=activity, start=now() - timedelta(days=10)
        )
        response = self.client.get(self.url + '?filter[upcoming]=1', user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(attributes['is-full'], False)
        self.assertEqual(attributes['theme'], activity.theme.name)
        self.assertEqual(attributes['expertise'], activity.expertise.name)
        self.assertEqual(attributes['slot-count'], 3)
        self.assertEqual(
            dateutil.parser.parse(attributes['start']),
            min([slot.start for slot in activity.slots.all() if slot.start > now()])
        )

        self.assertEqual(
            dateutil.parser.parse(attributes['end']),
            min([slot.end for slot in activity.slots.all() if slot.start > now()])
        )
        self.assertEqual(attributes['has-multiple-locations'], True)
        self.assertIsNone(attributes['location'])

    def test_date_preview_multiple_slots_single_location(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        location = GeolocationFactory.create()
        DateActivitySlotFactory.create_batch(3, activity=activity, location=location)
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(attributes['is-full'], False)
        self.assertEqual(attributes['theme'], activity.theme.name)
        self.assertEqual(attributes['expertise'], activity.expertise.name)
        self.assertEqual(attributes['slot-count'], 3)
        self.assertEqual(attributes['has-multiple-locations'], False)

        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_date_preview_multiple_slots_single_open(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create(activity=activity, status='draft', is_online=None)
        open_slot = DateActivitySlotFactory.create(activity=activity)

        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slot-count'], 1)
        self.assertEqual(attributes['has-multiple-locations'], False)

        self.assertEqual(
            attributes['location'],
            f'{open_slot.location.locality}, {open_slot.location.country.alpha2_code}'
        )

        self.assertEqual(dateutil.parser.parse(attributes['start']), open_slot.start)
        self.assertEqual(dateutil.parser.parse(attributes['end']), open_slot.end)

    def test_date_preview_multiple_slots_filtered(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="date")

        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create(activity=activity, start=now() + timedelta(days=14))
        DateActivitySlotFactory.create(activity=activity, start=now() + timedelta(days=21))
        current_slot = DateActivitySlotFactory.create(activity=activity, start=now() + timedelta(days=7))

        start = now()
        end = start + timedelta(days=12)
        response = self.client.get(
            self.url + '?filter[date]={},{}'.format(
                start.strftime('%Y-%m-%d'),
                end.strftime('%Y-%m-%d')
            )
        )
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['slot-count'], 1)

        self.assertEqual(attributes['has-multiple-locations'], False)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(dateutil.parser.parse(attributes['start']), current_slot.start)
        self.assertEqual(dateutil.parser.parse(attributes['end']), current_slot.end)

        location = current_slot.location
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_date_preview_multiple_slots_succeeded(self):
        activity = DateActivityFactory.create(slots=[])
        first = DateActivitySlotFactory.create(activity=activity, start=now() - timedelta(days=21))
        DateActivitySlotFactory.create(activity=activity, start=now() - timedelta(days=14))
        last = DateActivitySlotFactory.create(activity=activity, start=now() - timedelta(days=7))

        activity.status = 'succeeded'
        activity.save()

        response = self.client.get(self.url)
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['slot-count'], 0)

        self.assertEqual(attributes['has-multiple-locations'], True)
        self.assertEqual(attributes['is-online'], False)

        self.assertEqual(dateutil.parser.parse(attributes['start']), first.start)
        self.assertEqual(dateutil.parser.parse(attributes['end']), last.end)

    def test_date_preview_all_full(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create_batch(3, activity=activity, status='full')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['is-full'], True)

    def test_date_preview_is_online(self):
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create_batch(
            3, activity=activity, location=None, is_online=True, status='full'
        )
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['is-online'], True)

    def test_date_preview_matching(self):
        activity = DateActivityFactory.create(
            status='open',
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=activity,
            location=GeolocationFactory.create(position=Point(20.1, 10.1))
        )

        DateActivitySlotFactory.create(
            activity=activity
        )

        self.owner.favourite_themes.add(activity.theme)
        self.owner.skills.add(activity.expertise)
        self.owner.place = PlaceFactory.create(
            position=Point(20.0, 10.0)
        )
        self.owner.save()

        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['matching-properties']['theme'], True)
        self.assertEqual(attributes['matching-properties']['skill'], True)
        self.assertEqual(attributes['matching-properties']['location'], True)

    def test_deadline_preview(self):
        activity = DeadlineActivityFactory.create(status='open', is_online=False)
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(attributes['is-full'], None)
        self.assertEqual(attributes['theme'], activity.theme.name)
        self.assertEqual(attributes['expertise'], activity.expertise.name)
        self.assertEqual(attributes['slot-count'], None)
        self.assertEqual(attributes['has-multiple-locations'], False)
        self.assertEqual(attributes['contribution-duration'], {'period': 'once', 'value': 4.0})

        location = activity.location
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

        self.assertEqual(attributes['matching-properties']['theme'], False)
        self.assertEqual(attributes['matching-properties']['skill'], False)
        self.assertEqual(attributes['matching-properties']['location'], False)

    def test_deadline_preview_matching(self):
        activity = DeadlineActivityFactory.create(
            status='open',
            location=GeolocationFactory.create(position=Point(20.1, 10.1))
        )

        self.owner.favourite_themes.add(activity.theme)
        self.owner.skills.add(activity.expertise)
        self.owner.place = PlaceFactory.create(
            position=Point(20.0, 10.0)
        )
        self.owner.save()

        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']
        self.assertEqual(attributes['matching-properties']['theme'], True)
        self.assertEqual(attributes['matching-properties']['skill'], True)
        self.assertEqual(attributes['matching-properties']['location'], True)

    def test_funding_preview(self):
        activity = FundingFactory.create(status='open')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], True)
        self.assertEqual(attributes['is-full'], None)
        self.assertEqual(attributes['theme'], activity.theme.name)
        self.assertEqual(attributes['expertise'], None)
        self.assertEqual(attributes['slot-count'], None)
        self.assertEqual(attributes['has-multiple-locations'], False)

        location = activity.initiative.place
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_collect_preview(self):
        activity = CollectActivityFactory.create(status='open')
        response = self.client.get(self.url, user=self.owner)
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['slug'], activity.slug)
        self.assertEqual(attributes['title'], activity.title)
        self.assertEqual(attributes['initiative'], activity.initiative.title)
        self.assertEqual(attributes['status'], activity.status)
        self.assertEqual(attributes['team-activity'], activity.team_activity)
        self.assertEqual(attributes['is-online'], False)
        self.assertEqual(attributes['is-full'], None)
        self.assertEqual(attributes['theme'], activity.theme.name)
        self.assertEqual(attributes['expertise'], None)
        self.assertEqual(attributes['slot-count'], None)
        self.assertEqual(attributes['has-multiple-locations'], False)
        self.assertEqual(attributes['collect-type'], activity.collect_type.name)

        location = activity.location
        self.assertEqual(
            attributes['location'], f'{location.locality}, {location.country.alpha2_code}'
        )

    def test_collect_preview_dutch(self):
        activity = CollectActivityFactory.create(status='open')
        theme_translation = activity.theme.translations.get(
            language_code='nl'
        )

        collect_type_translation = activity.collect_type.translations.get(
            language_code='nl'
        )
        response = self.client.get(self.url, HTTP_X_APPLICATION_LANGUAGE='nl')
        attributes = response.json()['data'][0]['attributes']

        self.assertEqual(attributes['theme'], theme_translation.name)
        self.assertEqual(attributes['collect-type'], collect_type_translation.name)

    def test_search(self):
        text = 'consectetur adipiscing elit,'
        title = DeadlineActivityFactory.create(
            status="open", title=f'title with {text}',
        )
        description = DeadlineActivityFactory.create(
            status="open", description=json.dumps({'html': f'description with {text}', 'delta': ''}),
        )

        initiative_title = DeadlineActivityFactory.create(
            status="open", initiative=InitiativeFactory.create(title=f'title with {text}'),
        )
        initiative_story = DeadlineActivityFactory.create(
            status="open",
            initiative=InitiativeFactory.create(
                story=json.dumps({'html': f'story with {text}', 'delta': ''})
            ),
        )

        initiative_pitch = DeadlineActivityFactory.create(
            status="open", initiative=InitiativeFactory.create(pitch=f'pitch with {text}'),
        )

        slot_title = DateActivityFactory.create(status="open")
        DateActivitySlotFactory.create(activity=slot_title, title=f'slot title with {text}')

        response = self.client.get(
            f'{self.url}?filter[search]={text}',
        )

        data = json.loads(response.content)
        ids = [int(activity['id']) for activity in data['data']]

        self.assertTrue(title.pk in ids)
        self.assertTrue(description.pk in ids)
        self.assertTrue(initiative_title.pk in ids)
        self.assertTrue(initiative_pitch.pk in ids)
        self.assertTrue(initiative_story.pk in ids)
        self.assertTrue(slot_title.pk in ids)

        self.assertEqual(data['meta']['pagination']['count'], 6)

    def test_search_prefix(self):
        text = 'consectetur adipiscing elit,'
        title = DeadlineActivityFactory.create(
            status="open", title=f'title with {text}',
        )
        description = DeadlineActivityFactory.create(
            status="open",
            description=json.dumps(
                {'html': f'description with {text}', 'delta': ''}
            ),
        )

        initiative_title = DeadlineActivityFactory.create(
            status="open", initiative=InitiativeFactory.create(title=f'title with {text}'),
        )
        initiative_story = DeadlineActivityFactory.create(
            status="open",
            initiative=InitiativeFactory.create(
                story=json.dumps({'html': f'story with {text}', 'delta': ''})
            ),
        )

        initiative_pitch = DeadlineActivityFactory.create(
            status="open", initiative=InitiativeFactory.create(pitch=f'pitch with {text}'),
        )

        slot_title = DateActivityFactory.create(status="open")
        DateActivitySlotFactory.create(activity=slot_title, title=f'slot title with {text}')

        response = self.client.get(
            f'{self.url}?filter[search]={text[:10]}',
        )

        data = json.loads(response.content)
        ids = [int(activity['id']) for activity in data['data']]

        self.assertTrue(title.pk in ids)
        self.assertTrue(description.pk in ids)
        self.assertTrue(initiative_title.pk in ids)
        self.assertTrue(initiative_pitch.pk in ids)
        self.assertTrue(initiative_story.pk in ids)
        self.assertTrue(slot_title.pk in ids)

        self.assertEqual(data['meta']['pagination']['count'], 6)

    def test_sort_upcoming(self):
        today = now().date()
        first_date_activity = DateActivityFactory.create(pk=2, status='open', slots=[])
        second_date_activity = DateActivityFactory.create(pk=3, status='open', slots=[])
        activities = [
            DeadlineActivityFactory(
                pk=1, status='full', start=None, deadline=now() + timedelta(days=1)
            ),
            first_date_activity,
            second_date_activity,

            DeadlineActivityFactory(
                pk=4, status='open', start=today + timedelta(days=8), deadline=today + timedelta(days=10)
            ),
            CollectActivityFactory(
                pk=5, status='open', start=today + timedelta(days=9), end=today + timedelta(days=11)
            ),

            DeadlineActivityFactory(pk=7, status='open', start=now() + timedelta(days=2), deadline=None),
            DeadlineActivityFactory(pk=8, status='open', start=None, deadline=None),
        ]

        DateActivitySlotFactory.create(
            status='open', start=now() + timedelta(days=2), activity=first_date_activity
        )
        DateActivitySlotFactory.create(
            status='open', start=now() + timedelta(days=5), activity=first_date_activity
        )
        DateActivitySlotFactory.create(
            status='open', start=now() - timedelta(days=5), activity=first_date_activity
        )

        DateActivitySlotFactory.create(
            status='open', start=now() + timedelta(days=4), activity=second_date_activity
        )
        DateActivitySlotFactory.create(
            status='open', start=now() + timedelta(days=7), activity=second_date_activity
        )
        DateActivitySlotFactory.create(
            status='open', start=now() - timedelta(days=7), activity=second_date_activity
        )

        self.search({'upcoming': 1})

        self.assertEqual(
            [str(activity.pk) for activity in activities],
            [activity['id'] for activity in self.data['data']]
        )

    def test_sort_upcoming_exclude_full(self):
        InitiativePlatformSettings.objects.create(include_full_activities=False)

        today = now().date()
        first_date_activity = DateActivityFactory.create(status='open', slots=[])
        second_date_activity = DateActivityFactory.create(status='open', slots=[])
        activities = [
            first_date_activity,
            second_date_activity,

            DeadlineActivityFactory(status='open', deadline=today + timedelta(days=8)),
            CollectActivityFactory(status='open', end=today + timedelta(days=9)),


            DeadlineActivityFactory(
                status='open', start=now() - timedelta(days=1), deadline=None
            ),
            DeadlineActivityFactory(
                status='open', start=None, deadline=None
            ),
        ]

        DateActivitySlotFactory.create(
            status='open', start=now() + timedelta(days=2), activity=first_date_activity
        )
        DateActivitySlotFactory.create(
            status='open', start=now() + timedelta(days=5), activity=first_date_activity
        )
        DateActivitySlotFactory.create(
            status='open', start=now() - timedelta(days=5), activity=first_date_activity
        )

        DateActivitySlotFactory.create(
            status='open', start=now() + timedelta(days=4), activity=second_date_activity
        )
        DateActivitySlotFactory.create(
            status='open', start=now() + timedelta(days=7), activity=second_date_activity
        )
        DateActivitySlotFactory.create(
            status='open', start=now() - timedelta(days=7), activity=second_date_activity
        )
        DeadlineActivityFactory(
            status='full', start=None, deadline=now() + timedelta(days=1)
        ),

        self.search({'upcoming': 1})

        self.assertEqual(
            [str(activity.pk) for activity in activities],
            [activity['id'] for activity in self.data['data']]
        )

    def test_sort_upcoming_false(self):
        today = now().date()
        first_date_activity = DateActivityFactory.create(status='succeeded', slots=[])
        second_date_activity = DateActivityFactory.create(status='succeeded', slots=[])
        activities = [

            CollectActivityFactory(
                status='succeeded',
                start=today - timedelta(days=10),
                end=today - timedelta(days=1)
            ),

            second_date_activity,
            first_date_activity,

            DeadlineActivityFactory(
                status='succeeded', start=None, deadline=now() - timedelta(days=6)
            ),

            DeadlineActivityFactory(
                status='succeeded', start=None, deadline=now() - timedelta(days=10)
            ),

        ]

        DateActivitySlotFactory.create(
            status='finished', start=now() - timedelta(days=4), activity=first_date_activity
        )

        DateActivitySlotFactory.create(
            status='finished', start=now() - timedelta(days=5), activity=second_date_activity
        )
        DateActivitySlotFactory.create(
            status='finished', start=now() - timedelta(days=2), activity=second_date_activity
        )

        self.search({'upcoming': 0})

        self.assertEqual(
            [str(activity.pk) for activity in activities],
            [activity['id'] for activity in self.data['data']]
        )

    def test_sort_distance(self):
        amsterdam = GeolocationFactory.create(position=Point(4.922114, 52.362438))
        leiden = GeolocationFactory.create(position=Point(4.491056, 52.166758))
        texel = GeolocationFactory.create(position=Point(4.853281, 53.154617))
        lyutidol = GeolocationFactory.create(position=Point(23.676222, 43.068555))

        activity_amsterdam = DeadlineActivityFactory(status="open", location=amsterdam)
        activity_online1 = DeadlineActivityFactory(status="open", is_online=True)
        activity_leiden = DeadlineActivityFactory(status="open", location=leiden)
        activity_texel = DeadlineActivityFactory(status="open", location=texel)
        activity_online2 = DeadlineActivityFactory(status="open", is_online=True)
        activity_lyutidol = DeadlineActivityFactory(status="open", location=lyutidol)

        leiden_place = PlaceFactory.create(position=leiden.position)
        texel_place = PlaceFactory.create(position=texel.position)

        self.search(
            filter={'distance': '500km', 'is_online': '0'},
            sort='distance',
            place=leiden_place.pk
        )
        data = self.data['data']
        self.assertEqual(data[0]['id'], str(activity_leiden.id))
        self.assertEqual(data[1]['id'], str(activity_amsterdam.id))
        self.assertEqual(data[2]['id'], str(activity_texel.id))
        self.assertEqual(len(data), 3)

        # Widen search and search from Texel
        self.search(
            filter={'distance': '5000km', 'is_online': '0'},
            sort='distance',
            place=texel_place.pk
        )
        data = self.data['data']
        self.assertEqual(data[0]['id'], str(activity_texel.id))
        self.assertEqual(data[1]['id'], str(activity_amsterdam.id))
        self.assertEqual(data[2]['id'], str(activity_leiden.id))
        self.assertEqual(data[3]['id'], str(activity_lyutidol.id))
        self.assertEqual(len(data), 4)

        # With online
        self.search(
            filter={'distance': '500km'},
            sort='distance',
            place=leiden_place.pk
        )
        data = self.data['data']
        self.assertEqual(len(data), 5)
        self.assertEqual(data[0]['id'], str(activity_online1.id))
        self.assertEqual(data[1]['id'], str(activity_online2.id))
        self.assertEqual(data[2]['id'], str(activity_leiden.id))
        self.assertEqual(data[3]['id'], str(activity_amsterdam.id))
        self.assertEqual(data[4]['id'], str(activity_texel.id))

        # Any distance
        self.search(
            filter={'is_online': '0'},
            sort='distance',
            place=leiden_place.pk
        )
        data = self.data['data']
        self.assertEqual(data[0]['id'], str(activity_leiden.id))
        self.assertEqual(data[1]['id'], str(activity_amsterdam.id))
        self.assertEqual(data[2]['id'], str(activity_texel.id))
        self.assertEqual(data[3]['id'], str(activity_lyutidol.id))
        self.assertEqual(len(data), 4)

    def test_sort_date(self):
        today = now().date()
        activities = [
            DeadlineActivityFactory(
                status='open', start=now() + timedelta(days=1), deadline=now() + timedelta(days=1)
            ),
            DateActivityFactory.create(status='open', slots=[]),
            DateActivityFactory.create(status='open', slots=[]),
            DeadlineActivityFactory(status='open', deadline=today + timedelta(days=8)),
            CollectActivityFactory(status='open', end=today + timedelta(days=9)),
            DeadlineActivityFactory(
                status='open', start=None, deadline=None
            ),
        ]
        DateActivitySlotFactory.create(status='open', start=now() + timedelta(days=2), activity=activities[1])
        DateActivitySlotFactory.create(status='open', start=now() + timedelta(days=5), activity=activities[1])

        DateActivitySlotFactory.create(status='open', start=now() + timedelta(days=4), activity=activities[2])
        DateActivitySlotFactory.create(status='open', start=now() + timedelta(days=7), activity=activities[2])

        self.search({'upcoming': '1'}, 'date')

        self.assertEqual(
            [str(activity.pk) for activity in activities],
            [activity['id'] for activity in self.data['data']]
        )

    def test_filter_closed_segments(self):
        segment_type = SegmentTypeFactory.create(is_active=True, enable_search=True)
        open_segment = SegmentFactory.create(segment_type=segment_type, closed=False)
        closed_segment = SegmentFactory.create(segment_type=segment_type, closed=True)

        open = [
            DateActivityFactory.create(status='open'),
            CollectActivityFactory.create(status='open')
        ]
        for activity in open:
            activity.segments.add(open_segment)

        closed = [
            DateActivityFactory.create(status='open'),
            CollectActivityFactory.create(status='open')
        ]
        for activity in closed:
            activity.segments.add(closed_segment)

        self.search({})
        self.assertFound(open)

        user = BlueBottleUserFactory.create()
        user.segments.add(closed_segment)

        self.search({}, user=user)
        self.assertFound(open + closed)

        staff_user = BlueBottleUserFactory.create(is_staff=True)

        self.search({}, user=staff_user)
        self.assertFound(open + closed)

    def test_filter_type(self):
        matching = (
            DateActivityFactory.create_batch(3, status='open') +
            DeadlineActivityFactory.create_batch(2, status='open')
        )
        funding = FundingFactory.create_batch(1, status='open')
        deed = DeedFactory.create_batch(3, status='open')
        collect = CollectActivityFactory.create_batch(4, status='open')

        self.search({'activity-type': 'time'})

        self.assertFacets(
            'activity-type',
            {
                'time': (None, len(matching)),
                'funding': (None, len(funding)),
                'collect': (None, len(collect)),
                'deed': (None, len(deed)),

            }
        )

        self.assertFound(matching)

    def test_filter_type_missing(self):
        matching = (
            DateActivityFactory.create_batch(3, status='open') +
            DeadlineActivityFactory.create_batch(2, status='open')
        )
        funding = FundingFactory.create_batch(1, status='open')
        CollectActivityFactory.create_batch(4, status='cancelled')
        deed = DeedFactory.create_batch(3, status='open')

        self.search({'activity-type': 'time'})

        self.assertFacets(
            'activity-type',
            {
                'time': (None, len(matching)),
                'funding': (None, len(funding)),
                'collect': (None, 0),
                'deed': (None, len(deed)),

            }
        )

        self.assertFound(matching)

    def test_filter_segment(self):
        segment_type = SegmentTypeFactory.create(is_active=True, enable_search=True)
        matching_segment, other_segment = SegmentFactory.create_batch(2, segment_type=segment_type)

        matching = [
            DateActivityFactory.create(status='open'),
            CollectActivityFactory.create(status='open')
        ]
        for activity in matching:
            activity.segments.add(matching_segment)

        other = [
            DateActivityFactory.create(status='open'),
            CollectActivityFactory.create(status='open')
        ]
        for activity in other:
            activity.segments.add(other_segment)

        self.search({f'segment.{segment_type.slug}': matching_segment.pk})

        self.assertFacets(
            f'segment.{segment_type.slug}',
            {
                f'{matching_segment.pk}': (matching_segment.name, len(matching)),
                f'{other_segment.pk}': (other_segment.name, len(other))
            }
        )
        self.assertFound(matching)

    def test_filter_theme(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="theme")

        matching_theme, other_theme = ThemeFactory.create_batch(2)

        matching = DeedFactory.create_batch(3, status="open", theme=matching_theme)
        other = DeedFactory.create_batch(2, status="open", theme=other_theme)

        self.search({
            'theme': matching_theme.pk,
        })

        self.assertFacets(
            'theme',
            {
                str(matching_theme.pk): (matching_theme.name, len(matching)),
                str(other_theme.pk): (other_theme.name, len(other))
            }
        )
        self.assertFound(matching)

    def test_filter_theme_not_in_settings(self):
        matching_theme = ThemeFactory.create()
        other_theme = ThemeFactory.create()
        matching = DeedFactory.create_batch(3, status="open", theme=matching_theme)
        other = DeedFactory.create_batch(2, status="open", theme=other_theme)

        self.search({
            'theme': matching_theme.pk,
        })

        self.assertFacets(
            'theme',
            {
                str(matching_theme.pk): (matching_theme.name, len(matching)),
                str(other_theme.pk): (other_theme.name, len(other))
            }
        )
        self.assertFound(matching)

    def test_filter_theme_no_matches(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="theme")
        ActivitySearchFilter.objects.create(settings=settings, type="country")

        matching_theme, other_theme = ThemeFactory.create_batch(2)

        DeedFactory.create_batch(3, status="open", theme=matching_theme)
        DeedFactory.create_batch(2, status="open", theme=other_theme)

        self.search({
            'theme': matching_theme.pk,
            'country': 'something-that-does-not-match'
        })

        self.assertFacets(
            'theme',
            {
                str(matching_theme.pk): (matching_theme.name, 0),
            }
        )
        self.assertFound([])

    def test_filter_theme_dutch(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="theme")

        matching_theme, other_theme = ThemeFactory.create_batch(2)

        matching = DeedFactory.create_batch(3, status="open", theme=matching_theme)
        other = DeedFactory.create_batch(2, status="open", theme=other_theme)

        self.search(
            {'theme': matching_theme.pk},
            headers={'HTTP_X_APPLICATION_LANGUAGE': 'nl'}
        )

        matching_theme_translation = matching_theme.translations.get(
            language_code='nl'
        )
        other_theme_translation = other_theme.translations.get(
            language_code='nl'
        )

        self.assertFacets(
            'theme',
            {
                str(matching_theme.pk): (matching_theme_translation.name, len(matching)),
                str(other_theme.pk): (other_theme_translation.name, len(other))
            }
        )
        self.assertFound(matching)

    def test_filter_initiative(self):

        initiator = BlueBottleUserFactory.create()
        activity_manager = BlueBottleUserFactory.create()
        draft_owner = BlueBottleUserFactory.create()
        random_user = BlueBottleUserFactory.create()

        initiative = InitiativeFactory.create(status='approved', owner=initiator)
        initiative.activity_managers.add(activity_manager)

        open = DeedFactory.create(status="open", initiative=initiative)
        draft = DeedFactory.create(status="draft", initiative=initiative, owner=draft_owner)
        DeedFactory.create(status="deleted", initiative=initiative)
        DeedFactory.create(status="open")

        self.search({'initiative.id': initiative.id}, user=initiator)
        self.assertFound([open, draft])

        self.search({'initiative.id': initiative.id}, user=activity_manager)
        self.assertFound([open, draft])

        self.search({'initiative.id': initiative.id}, user=draft_owner)
        self.assertFound([open, draft])

        self.search({'initiative.id': initiative.id}, user=random_user)
        self.assertFound([open])

        self.search({'initiative.id': initiative.id})
        self.assertFound([open])

    def test_filter_upcoming(self):
        matching = (
            DeadlineActivityFactory.create_batch(2, status='open') +
            DeadlineActivityFactory.create_batch(2, status='full')
        )
        DeadlineActivityFactory.create_batch(2, status='succeeded')
        DeadlineActivityFactory.create_batch(2, status='draft')
        DeadlineActivityFactory.create_batch(2, status='needs_work')

        self.search({'upcoming': 1})
        self.assertFound(matching)

    def test_filter_upcoming_hide_full(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.include_full_activities = False
        initiative_settings.save()
        matching = DeadlineActivityFactory.create_batch(2, status='open')
        DeadlineActivityFactory.create_batch(2, status='full')
        DeadlineActivityFactory.create_batch(2, status='succeeded')
        DeadlineActivityFactory.create_batch(2, status='draft')
        DeadlineActivityFactory.create_batch(2, status='needs_work')

        self.search({'upcoming': 1})
        self.assertFound(matching)

    def test_no_filter(self):
        matching = (
            DeadlineActivityFactory.create_batch(2, status='open') +
            DeadlineActivityFactory.create_batch(2, status='full') +
            DeadlineActivityFactory.create_batch(2, status='full') +
            FundingFactory.create_batch(2, status='partially_funded')
        )
        DeadlineActivityFactory.create_batch(2, status='draft')
        DeadlineActivityFactory.create_batch(2, status='needs_work')
        DeadlineActivityFactory.create_batch(2, status='needs_work')

        self.search({})

        self.assertFound(matching)

    def test_filter_team(self):
        InitiativePlatformSettings.objects.create(activity_search_filters=['team_activity'])

        matching = DeadlineActivityFactory.create_batch(2, status="open", team_activity='teams')
        other = DeadlineActivityFactory.create_batch(3, status="open", team_activity='individuals')

        self.search({'team_activity': 'teams'})

        self.assertFacets(
            'team_activity',
            {'teams': ('With your team', len(matching)), 'individuals': ('As an individual', len(other))}
        )
        self.assertFound(matching)

    def test_filter_team_no_matching(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="theme_activity")
        ActivitySearchFilter.objects.create(settings=settings, type="country")

        DeadlineActivityFactory.create_batch(2, status="open", team_activity='teams')
        DeadlineActivityFactory.create_batch(3, status="open", team_activity='individuals')

        self.search({
            'team_activity': 'teams',
            'country': 'something-that-does-not-match'
        })

        self.assertFacets(
            'team_activity',
            {'teams': ('With your team', 0)}
        )
        self.assertFound([])

    def test_filter_online(self):
        matching = DeadlineActivityFactory.create_batch(2, status="open", is_online=True)
        other = DeadlineActivityFactory.create_batch(3, status="open", is_online=False)

        self.search({'is_online': '1'})

        self.assertFacets(
            'is_online',
            {1: ('Online/remote', len(matching)), 0: ('In-person', len(other))}
        )
        self.assertFound(matching)

    def test_filter_category(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="category")

        matching_category = CategoryFactory.create()
        other_category = CategoryFactory.create()

        matching = DeadlineActivityFactory.create_batch(2, status='open')
        for activity in matching:
            activity.categories.add(matching_category)

        other = DeadlineActivityFactory.create_batch(3, status='open')
        for activity in other:
            activity.categories.add(other_category)

        self.search({'category': matching_category.pk})

        self.assertFacets(
            'category',
            {
                str(matching_category.pk): (matching_category.title, len(matching)),
                str(other_category.pk): (other_category.title, len(other))
            }
        )
        self.assertFound(matching)

    def test_filter_category_not_in_settings(self):
        matching_category = CategoryFactory.create()
        other_category = CategoryFactory.create()

        matching = DeadlineActivityFactory.create_batch(2, status='open')
        for activity in matching:
            activity.categories.add(matching_category)

        other = DeadlineActivityFactory.create_batch(3, status='open')
        for activity in other:
            activity.categories.add(other_category)

        self.search({'category': matching_category.pk})

        self.assertFacets(
            'category',
            {
                str(matching_category.pk): (matching_category.title, len(matching)),
                str(other_category.pk): (other_category.title, len(other))
            }
        )
        self.assertFound(matching)

    def test_filter_category_without_setting(self):
        InitiativePlatformSettings.objects.create()
        matching_category = CategoryFactory.create()
        other_category = CategoryFactory.create()

        matching = DeadlineActivityFactory.create_batch(2, status='open')
        for activity in matching:
            activity.categories.add(matching_category)

        other = DeadlineActivityFactory.create_batch(3, status='open')
        for activity in other:
            activity.categories.add(other_category)

        self.search({'category': matching_category.pk})

        self.assertFacets(
            'category',
            {
                str(matching_category.pk): (matching_category.title, len(matching)),
                str(other_category.pk): (other_category.title, len(other))
            }
        )
        self.assertFound(matching)

    def test_filter_skill(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="skill")

        matching_skill = SkillFactory.create()
        other_skill = SkillFactory.create()

        matching = DeadlineActivityFactory.create_batch(
            2,
            expertise=matching_skill,
            status='open',
        )

        other = DeadlineActivityFactory.create_batch(
            3,
            expertise=other_skill,
            status='open',
        )

        self.search({'skill': matching_skill.pk})

        self.assertFacets(
            'skill',
            {
                str(matching_skill.pk): (matching_skill.name, len(matching)),
                str(other_skill.pk): (other_skill.name, len(other))
            }
        )
        self.assertFound(matching)

    def test_office_facet(self):
        madrid = LocationFactory.create(name='Madrid')

        DeadlineActivityFactory.create_batch(
            2,
            office_location=madrid,
            status="open",
        )

        ltyutidol = LocationFactory.create(name='Лютидол')

        DeadlineActivityFactory.create_batch(
            3,
            office_location=ltyutidol,
            status="open",
        )

        self.search({
            'office': madrid.id
        })

        self.assertFacets(
            "office",
            {
                str(madrid.pk): (madrid.name, 2),
                str(ltyutidol.pk): (ltyutidol.name, 3)
            }
        )

    def test_filter_country(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="country")

        matching_country = CountryFactory.create()
        other_country = CountryFactory.create()

        matching = DeadlineActivityFactory.create_batch(
            2,
            office_location=LocationFactory.create(country=matching_country),
            status='open',
        )

        other = DeadlineActivityFactory.create_batch(
            3,
            office_location=LocationFactory.create(country=other_country),
            status='open',
        )

        self.search({'country': matching_country.pk})

        self.assertFacets(
            'country',
            {
                str(matching_country.pk): (matching_country.name, len(matching)),
                str(other_country.pk): (other_country.name, len(other))
            }
        )
        self.assertFound(matching)

    def test_more_country_facets(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="country")

        countries = CountryFactory.create_batch(12)
        matching = []
        for country in countries:
            location = GeolocationFactory.create(country=country)
            matching.append(DeadlineActivityFactory.create(location=location, status='open'))

        self.search({})
        self.assertEqual(len(self.data['meta']['facets']['country']), 12)
        self.assertFound(matching)

    def test_filter_country_slots(self):
        settings = InitiativePlatformSettings.objects.create()
        ActivitySearchFilter.objects.create(settings=settings, type="country")

        matching_country = CountryFactory.create()
        other_country = CountryFactory.create()

        matching = DateActivityFactory.create_batch(
            2,
            status='open',
        )
        for activity in matching:
            DateActivitySlotFactory.create_batch(
                2,
                activity=activity,
                location=GeolocationFactory.create(country=matching_country)
            )

        other = DateActivityFactory.create_batch(
            3,
            status='open',
        )
        for activity in other:
            DateActivitySlotFactory.create_batch(
                2,
                activity=activity,
                location=GeolocationFactory.create(country=other_country)
            )

        self.search({'country': matching_country.pk})

        self.assertFacets(
            'country',
            {
                str(matching_country.pk): (matching_country.name, len(matching)),
                str(other_country.pk): (other_country.name, len(other))
            }
        )
        self.assertFound(matching)

    def test_filter_highlight(self):
        matching = DeadlineActivityFactory.create_batch(
            2,
            highlight=True,
            status='open',
        )

        other = DeadlineActivityFactory.create_batch(
            3,
            highlight=False,
            status='open',
        )
        self.search({'highlight': 'true'})

        self.assertFacets(
            'highlight',
            {1: ('Yes', len(matching)), 0: ('No', len(other))}
        )
        self.assertFound(matching)

    def test_filter_date(self):
        matching = [
            DeadlineActivityFactory.create(status="open", start='2025-04-01', deadline='2025-04-02'),
            DeadlineActivityFactory.create(status="open", start='2025-04-01', deadline='2025-04-03'),
            DeedFactory.create(status="open", start='2025-04-05', end='2025-04-07'),
            CollectActivityFactory.create(status="open", start='2025-04-05', end='2025-04-07'),
        ]

        DeadlineActivityFactory.create(status="open", start='2025-05-01', deadline='2025-05-02')
        DeadlineActivityFactory.create(status="open", start='2025-05-01', deadline='2025-05-03')
        DeedFactory.create(status="open", start='2025-05-05', end='2025-05-07')
        CollectActivityFactory.create(status="open", start='2025-05-05', end='2025-05-07')

        self.search({'date': '2025-04-01,2025-04-08'})

        self.assertFacets(
            'date', {}
        )

        self.assertFound(matching)

    def test_filter_past_dates(self):
        activity1 = DateActivityFactory.create(status="succeeded")
        activity2 = DateActivityFactory.create(status="succeeded")
        activity3 = DateActivityFactory.create(status="succeeded")
        activity4 = DeadlineActivityFactory.create(status="succeeded", start='2022-04-15', deadline='2022-05-15')
        DeadlineActivityFactory.create(status="succeeded", start='2022-03-01', deadline='2022-06-01')

        DateActivitySlotFactory.create(activity=activity1, start=datetime.datetime(2022, 5, 3, tzinfo=UTC))
        DateActivitySlotFactory.create(activity=activity1, start=datetime.datetime(2022, 5, 25, tzinfo=UTC))
        DateActivitySlotFactory.create(activity=activity1, start=datetime.datetime(2022, 6, 3, tzinfo=UTC))

        DateActivitySlotFactory.create(activity=activity2, start=datetime.datetime(2022, 5, 30, tzinfo=UTC))
        DateActivitySlotFactory.create(activity=activity2, start=datetime.datetime(2022, 5, 25, tzinfo=UTC))
        DateActivitySlotFactory.create(activity=activity2, start=datetime.datetime(2022, 4, 25, tzinfo=UTC))

        DateActivitySlotFactory.create(activity=activity3, start=datetime.datetime(2022, 6, 3, tzinfo=UTC))
        DateActivitySlotFactory.create(activity=activity3, start=datetime.datetime(2022, 4, 23, tzinfo=UTC))

        matching = [
            activity1, activity2, activity4
        ]

        self.search({'date': '2022-05-01,2022-05-31'})
        self.assertFound(matching)
        self.assertEqual(
            self.data['data'][0]['attributes']['end'],
            "2022-05-30T02:00:00+00:00"
        )
        self.assertEqual(
            self.data['data'][1]['attributes']['end'],
            "2022-05-25T02:00:00+00:00"
        )
        self.assertEqual(
            self.data['data'][2]['attributes']['end'],
            "2022-05-15"
        )

    def test_filter_distance(self):
        lat = 52.0
        lon = 10

        place = PlaceFactory.create(
            position=Point(lon, lat)
        )
        matching = [
            DateActivityFactory.create(status="open", slots=[]),
            DateActivityFactory.create(status="open", slots=[]),
            DeadlineActivityFactory.create(
                status="open", location=GeolocationFactory.create(position=Point(lon + 0.1, lat + 0.1))
            ),
            DeadlineActivityFactory.create(
                status="open", location=GeolocationFactory.create(position=Point(lon - 0.1, lat - 0.1))
            ),
            CollectActivityFactory.create(
                status="open", location=GeolocationFactory.create(position=Point(lon + 0.1, lat + 0.1))
            ),
        ]

        DateActivitySlotFactory.create(
            status="draft",
            activity=matching[0],
            location=GeolocationFactory.create(position=Point(lon + 0.05, lat + 0.05))
        )
        DateActivitySlotFactory.create(
            status="draft",
            activity=matching[1],
            location=GeolocationFactory.create(position=Point(lon - 0.05, lat - 0.05))
        )

        further = DeadlineActivityFactory.create(
            status="open",
            location=GeolocationFactory.create(position=Point(lon - 1, lat - 1))
        )
        furthest = DeadlineActivityFactory.create(
            status="open",
            location=GeolocationFactory.create(position=Point(lon - 2, lat - 2))
        )

        other = DateActivityFactory.create(slots=[])
        DateActivitySlotFactory.create(
            activity=other,
            location=GeolocationFactory.create(position=Point(lon + 2, lat + 2))
        )

        DeadlineActivityFactory.create(
            status="open",
            is_online=True
        )

        self.search({'distance': '100km', 'is_online': '0'}, place=place.pk)
        self.assertFacets(
            'distance', {}
        )
        self.assertFound(matching)

        self.search({'distance': '200km', 'is_online': '0'}, place=place.pk)
        self.assertFound(matching + [further])

        self.search({'distance': '200mi', 'is_online': '0'}, place=place.pk)
        self.assertFound(matching + [further, furthest])

    def test_filter_distance_with_online(self):
        amsterdam = Point(4.922114, 52.362438)
        leiden = Point(4.491056, 52.166758)
        lyutidol = Point(23.676222, 43.068555)

        place = PlaceFactory(position=leiden)
        matching = [
            DateActivityFactory.create(status="open", slots=[]),
            DateActivityFactory.create(status="open", slots=[]),
            DeadlineActivityFactory.create(
                status="open", location=GeolocationFactory.create(position=leiden),
            ),
            DeadlineActivityFactory.create(
                status="open", location=GeolocationFactory.create(position=amsterdam),
            ),
            DeadlineActivityFactory.create(
                status="open", is_online=True,
            ),
            DeedFactory.create(status="open"),
            FundingFactory.create(status="open"),
            CollectActivityFactory.create(status="open", location=None)

        ]

        DateActivitySlotFactory.create(
            activity=matching[0],
            location=GeolocationFactory.create(position=leiden)
        )
        DateActivitySlotFactory.create(
            activity=matching[1],
            location=GeolocationFactory.create(position=amsterdam)
        )

        DeadlineActivityFactory.create(
            status="open", location=GeolocationFactory.create(position=lyutidol)
        )
        DeadlineActivityFactory.create(
            status="open", location=GeolocationFactory.create(position=lyutidol)
        )

        other = DateActivityFactory.create(status="open", slots=[])
        DateActivitySlotFactory.create(
            activity=other,
            location=GeolocationFactory.create(position=lyutidol)
        )

        self.search({'distance': '100km'}, place=place.pk)

        self.assertFacets(
            'distance', {}
        )

        self.assertFound(matching)

    def test_filter_office_restriction(self):
        office = LocationFactory.create(subregion=OfficeSubRegionFactory.create())
        within_sub_region = LocationFactory.create(subregion=office.subregion)
        within_region = LocationFactory.create(
            subregion=OfficeSubRegionFactory(region=office.subregion.region)
        )

        matching = [
            DeadlineActivityFactory.create(
                status="open", office_location=office, office_restriction='office'
            ),
            DeadlineActivityFactory.create(
                status="open", office_location=within_region, office_restriction='office_region'
            ),
            DeadlineActivityFactory.create(
                status="open", office_location=within_sub_region, office_restriction='office_subregion'
            ),
            DeadlineActivityFactory.create(
                status="open", office_location=LocationFactory.create(), office_restriction='all'
            ),
        ]

        DeadlineActivityFactory.create(
            status="open", office_location=LocationFactory.create(), office_restriction='office'
        )
        DeadlineActivityFactory.create(
            status="open", office_location=within_region, office_restriction='office'
        )
        DeadlineActivityFactory.create(
            status="open", office_location=within_region, office_restriction='office_subregion'
        )

        user = BlueBottleUserFactory.create(location=office)

        self.search({'office_restriction': '1'}, user=user)

        self.assertFacets(
            'distance', {}
        )

        self.assertFound(matching)


class ActivityRelatedImageAPITestCase(BluebottleTestCase):
    def setUp(self):
        super(ActivityRelatedImageAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        self.funding = FundingFactory.create(
            owner=self.owner,
        )
        self.related_image_url = reverse('related-activity-image-list')

        file_path = './bluebottle/files/tests/files/test-image.png'

        with open(file_path, 'rb') as test_file:
            response = self.client.post(
                reverse('image-list'),
                test_file.read(),
                content_type="image/png",
                format=None,
                HTTP_CONTENT_DISPOSITION='attachment; filename="some_file.jpg"',
                user=self.owner
            )

        self.file_data = json.loads(response.content)

    def test_create(self):
        data = {
            'data': {
                'type': 'related-activity-images',
                'relationships': {
                    'image': {
                        'data': {
                            'type': 'images',
                            'id': self.file_data['data']['id']
                        }
                    },
                    'resource': {
                        'data': {
                            'type': 'activities/fundings',
                            'id': self.funding.pk,
                        }
                    }
                }
            }
        }
        response = self.client.post(
            self.related_image_url,
            data=json.dumps(data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            response.json()['included'][1]['attributes']['links']['large'].split('?')[0],
            u'/api/activities/{}/related-image/600'.format(response.json()['data']['id'])
        )

    def test_create_non_owner(self):
        data = {
            'data': {
                'type': 'related-activity-images',
                'relationships': {
                    'image': {
                        'data': {
                            'type': 'images',
                            'id': self.file_data['data']['id']
                        }
                    },
                    'resource': {
                        'data': {
                            'type': 'activities/fundings',
                            'id': self.funding.pk,
                        }
                    }
                }
            }
        }
        response = self.client.post(
            self.related_image_url,
            data=json.dumps(data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ContributionListAPITestCase(BluebottleTestCase):
    def setUp(self):
        super(ContributionListAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create()
        admin = BlueBottleUserFactory.create(is_staff=True)

        activity = DateActivityFactory.create()

        slot1 = DateActivitySlotFactory.create(
            start=now() - timedelta(days=2),
            activity=activity
        )
        slot2 = DateActivitySlotFactory.create(
            start=now() + timedelta(days=2),
            activity=activity
        )

        registration = DateRegistrationFactory.create(user=self.user, activity=activity)
        DateParticipantFactory.create(slot=slot1, registration=registration)
        DateParticipantFactory.create(slot=slot2, registration=registration)

        deadline = DeadlineActivityFactory.create(
            start=(now() - timedelta(days=4, hours=1)).date(),
        )

        DeadlineParticipantFactory.create(
            user=self.user,
            activity=deadline,
            as_user=admin
        )

        deed = DeedFactory.create(
            start=(now() + timedelta(days=2)).date(),
        )
        DeedParticipantFactory.create(user=self.user, activity=deed)

        collect = CollectActivityFactory.create(
            start=(now() + timedelta(days=2)).date(),
        )
        CollectContributorFactory.create(user=self.user, activity=collect)

        DeadlineParticipantFactory.create()
        DonorFactory.create()
        DeedParticipantFactory.create()
        CollectContributorFactory.create()

        self.url = reverse('contribution-list')

    def test_get_upcoming(self):
        response = self.client.get(
            self.url + "?filter[upcoming]=1",
            user=self.user
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data['data']), 3)

        self.assertEqual(
            data['data'][0]['type'],
            'contributions'
        )

        for contribution in data['data']:
            contributor = contribution['relationships']['contributor']['data']
            self.assertTrue(
                contributor['type'] in (
                    'contributors/time-based/date-participants',
                    'contributors/collect/contributors',
                    'contributors/deeds/participants',
                    'contributors/donations',
                    'contributors/time-based/deadline-participants',
                )
            )

    def test_get_past(self):
        response = self.client.get(
            self.url + "?filter[upcoming]=0",
            user=self.user
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data['data']), 2)

        self.assertEqual(
            data['data'][0]['type'],
            'contributions'
        )

        for contribution in data['data']:
            contributor = contribution['relationships']['contributor']['data']
            self.assertTrue(
                contributor['type'] in (
                    'contributors/time-based/date-participants',
                    'contributors/collect/contributors',
                    'contributors/deeds/participants',
                    'contributors/donations',
                    'contributors/time-based/deadline-participants',
                )
            )

    def test_get_anonymous(self):
        response = self.client.get(
            self.url
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_other_user(self):
        response = self.client.get(
            self.url,
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data['data']), 0)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
)
class ActivityLocationAPITestCase(APITestCase):
    model = Activity

    def setUp(self):
        self.user = BlueBottleUserFactory.create(
            location=LocationFactory.create(subregion=OfficeSubRegionFactory.create())
        )

        CollectActivityFactory.create(status='succeeded')
        CollectActivityFactory.create(
            status='succeeded',
            office_location=LocationFactory.create(
                subregion=self.user.location.subregion
            )
        )
        CollectActivityFactory.create(
            status='succeeded',
            office_location=LocationFactory.create(
                subregion=OfficeSubRegionFactory(region=self.user.location.subregion.region)
            )
        )
        DeadlineActivityFactory.create(status='succeeded')
        DeadlineActivityFactory.create(
            status='succeeded',
            office_location=LocationFactory.create(
                subregion=self.user.location.subregion
            )
        )
        DeadlineActivityFactory.create(
            status='succeeded',
            office_location=LocationFactory.create(
                subregion=OfficeSubRegionFactory(region=self.user.location.subregion.region)
            )
        )

        date_activity = DateActivityFactory.create(status="succeeded")
        slot = date_activity.slots.first()
        date_activity.slots.add(DateActivitySlotFactory.create(
            activity=date_activity,
            location_id=slot.location_id
        ))

        self.url = reverse('activity-location-list')

    def test_get(self):
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(7)
        self.assertAttribute('position')
        self.assertRelationship('activity')

    def test_get_anon(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(7)
        self.assertAttribute('position')
        self.assertRelationship('activity')

    def test_get_region(self):
        self.url += '?filter[type]=office_region'
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(4)
        self.assertAttribute('position')
        self.assertRelationship('activity')

    def test_get_subregion(self):
        self.url += '?filter[type]=office_subregion'
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(2)
        self.assertAttribute('position')
        self.assertRelationship('activity')

    def test_get_closed_platform(self):
        with self.closed_site():
            self.perform_get()
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get_closed_platform_logged_in(self):
        with self.closed_site():
            self.perform_get(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_200_OK)
