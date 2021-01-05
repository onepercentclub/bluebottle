from builtins import str
import json
from datetime import timedelta
import dateutil

from django.contrib.auth.models import Group, Permission
from django.contrib.gis.geos import Point
from django.test import tag
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now
from django_elasticsearch_dsl.test import ESTestCase
from rest_framework import status
from bluebottle.files.tests.factories import ImageFactory

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory, DateParticipantFactory, PeriodParticipantFactory
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.tests.factories import SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory, GeolocationFactory, PlaceFactory, CountryFactory
from bluebottle.test.factory_models.projects import ProjectThemeFactory
from bluebottle.test.factory_models.tasks import SkillFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class ActivityListSearchAPITestCase(ESTestCase, BluebottleTestCase):
    def setUp(self):
        super(ActivityListSearchAPITestCase, self).setUp()

        self.client = JSONAPITestClient()
        self.url = reverse('activity-list')
        self.owner = BlueBottleUserFactory.create()

    def test_images(self):
        DateActivityFactory.create(
            owner=self.owner, review_status='approved', image=ImageFactory.create()
        )
        PeriodActivityFactory.create(review_status='approved', image=ImageFactory.create())
        FundingFactory.create(review_status='approved', image=ImageFactory.create())

        response = self.client.get(self.url, user=self.owner)

        for activity in response.json()['data']:
            self.assertEqual(
                activity['relationships']['image']['data']['type'],
                'images'
            )

    def test_no_filter(self):
        succeeded = DateActivityFactory.create(
            owner=self.owner, status='succeeded'
        )
        open = DateActivityFactory.create(status='open')
        DateActivityFactory.create(status='submitted')
        DateActivityFactory.create(status='closed')
        DateActivityFactory.create(status='cancelled')

        response = self.client.get(self.url, user=self.owner)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][1]['id'], str(succeeded.pk))
        self.assertEqual(data['data'][0]['id'], str(open.pk))

        self.assertTrue('meta' in data['data'][0])

    def test_anonymous(self):
        succeeded = DateActivityFactory.create(
            owner=self.owner, status='succeeded'
        )
        open = DateActivityFactory.create(status='open')
        DateActivityFactory.create(status='submitted')
        DateActivityFactory.create(status='closed')

        response = self.client.get(self.url)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][1]['id'], str(succeeded.pk))
        self.assertEqual(data['data'][0]['id'], str(open.pk))

        self.assertTrue('meta' in data['data'][0])

    def test_filter_owner(self):
        DateActivityFactory.create(owner=self.owner, status='open')
        DateActivityFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['relationships']['owner']['data']['id'], str(self.owner.pk))

    def test_only_owner_permission(self):
        DateActivityFactory.create(owner=self.owner, status='open')
        DateActivityFactory.create(status='open')

        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_activity')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_activity')
        )

        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)

        self.assertEqual(data['data'][0]['relationships']['owner']['data']['id'], str(self.owner.pk))

    def test_initiative_location(self):
        location = LocationFactory.create()
        initiative = InitiativeFactory.create(status='open', location=location)
        activity = DateActivityFactory.create(status='open', initiative=initiative)
        DateActivityFactory.create(status='open')

        response = self.client.get(
            self.url + '?filter[initiative_location.id]={}'.format(location.pk),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(activity.pk))

    def test_activity_date_filter(self):
        next_month = now() + dateutil.relativedelta.relativedelta(months=1)
        after = now() + dateutil.relativedelta.relativedelta(months=2)

        event = DateActivityFactory.create(
            status='open',
            start=next_month
        )
        DateActivityFactory.create(
            status='open',
            start=after
        )

        assignment = PeriodActivityFactory.create(
            status='open',
            deadline=next_month
        )
        PeriodActivityFactory.create(
            status='open',
            deadline=after
        )

        # Feature is not dealing with time. Disabling timezone check for test
        funding = FundingFactory.create(
            status='open',
            deadline=next_month
        )
        FundingFactory.create(
            status='open',
            deadline=after
        )

        start = next_month - dateutil.relativedelta.relativedelta(weeks=2)
        end = next_month + dateutil.relativedelta.relativedelta(weeks=2)
        response = self.client.get(
            self.url + '?filter[start]={}-{}-{}&filter[end]={}-{}-{}'.format(
                start.year, start.month, start.day,
                end.year, end.month, end.day),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 5)

        found = [item['id'] for item in data['data']]
        self.assertTrue(str(event.pk) in found)
        self.assertTrue(str(assignment.pk) in found)
        self.assertTrue(str(funding.pk) in found)

        start = after - dateutil.relativedelta.relativedelta(weeks=2)
        end = after + dateutil.relativedelta.relativedelta(weeks=2)

        response = self.client.get(
            self.url + '?filter[start]={}-{}-{}&filter[end]={}-{}-{}'.format(
                start.year, start.month, start.day,
                end.year, end.month, end.day),
            user=self.owner
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 3)

        found = [item['id'] for item in data['data']]
        self.assertTrue(str(event.pk) not in found)
        self.assertTrue(str(assignment.pk) not in found)
        self.assertTrue(str(funding.pk) not in found)

    def test_filter_segment(self):
        segment = SegmentFactory.create()
        first = DateActivityFactory.create(
            status='open',
        )
        first.segments.add(segment)

        DateActivityFactory.create(
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[segment.{}]={}'.format(
                segment.type.slug, segment.pk
            ),
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(first.pk))

    def test_filter_segment_mismatch(self):
        first = DateActivityFactory.create(
            status='open',
        )
        first_segment = SegmentFactory.create()
        first.segments.add(first_segment)
        second_segment = SegmentFactory.create()
        first.segments.add(second_segment)

        DateActivityFactory.create(
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[segment.{}]={}'.format(
                first_segment.type.slug, second_segment.pk
            ),
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 0)

    def test_search(self):
        first = DateActivityFactory.create(
            title='Lorem ipsum dolor sit amet',
            description="Lorem ipsum",
            status='open'
        )
        second = DateActivityFactory.create(title='Lorem ipsum dolor sit amet', status='open')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(first.pk))
        self.assertEqual(data['data'][1]['id'], str(second.pk))

    def test_search_different_type(self):
        first = DateActivityFactory.create(
            title='Lorem ipsum dolor sit amet',
            description="Lorem ipsum",
            status='open'
        )
        second = FundingFactory.create(title='Lorem ipsum dolor sit amet', status='open')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(first.pk))
        self.assertEqual(data['data'][0]['type'], 'activities/time-based/dates')
        self.assertEqual(data['data'][1]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['type'], 'activities/fundings')

    def test_search_boost(self):
        first = DateActivityFactory.create(
            title='Something else',
            description='Lorem ipsum dolor sit amet',
            status='open'
        )
        second = DateActivityFactory.create(
            title='Lorem ipsum dolor sit amet',
            description="Something else",
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_search_formatted_address(self):
        location = GeolocationFactory.create(formatted_address='Roggeveenstraat')
        first = DateActivityFactory.create(
            location=location,
            status='open'
        )
        second = DateActivityFactory.create(
            title='Roggeveenstraat',
            status='open'
        )
        DateActivityFactory.create(
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[search]=Roggeveenstraat',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_search_initiative_title(self):
        first = DateActivityFactory.create(
            initiative=InitiativeFactory.create(title='Test title'),
            status='open'
        )
        second = DateActivityFactory.create(
            title='Test title',
            status='open'
        )
        DateActivityFactory.create(
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[search]=test title',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_search_segment_name(self):
        first = DateActivityFactory.create(
            status='open',
        )
        first.segments.add(SegmentFactory(name='Online Marketing'))

        DateActivityFactory.create(
            status='open'
        )

        response = self.client.get(
            self.url + '?filter[search]=marketing',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(first.pk))

    def test_sort_title(self):
        second = DateActivityFactory.create(title='B: something else', status='open')
        first = DateActivityFactory.create(title='A: something', status='open')
        third = DateActivityFactory.create(title='C: More', status='open')

        response = self.client.get(
            self.url + '?sort=alphabetical',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)
        self.assertEqual(data['data'][0]['id'], str(first.pk))
        self.assertEqual(data['data'][1]['id'], str(second.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))

    def test_sort_activity_date(self):
        first = DateActivityFactory.create(
            status='open',
            start=now() + timedelta(days=10)
        )

        second = FundingFactory.create(
            status='open',
            deadline=now() + timedelta(days=9)
        )
        third = PeriodActivityFactory.create(
            status='open',
            deadline=now() + timedelta(days=11)
        )

        response = self.client.get(
            self.url + '?sort=date',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)

        self.assertEqual(data['data'][0]['id'], str(third.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))
        self.assertEqual(data['data'][2]['id'], str(second.pk))

    def test_sort_matching_popularity(self):
        first = DateActivityFactory.create(status='open')
        second = DateActivityFactory.create(status='open')
        DateParticipantFactory.create(
            activity=second,
            created=now() - timedelta(days=7),
        )

        third = DateActivityFactory.create(status='open')
        DateParticipantFactory.create(
            activity=third,
            created=now() - timedelta(days=5),
        )

        fourth = DateActivityFactory.create(status='open')
        DateParticipantFactory.create(
            activity=fourth,
            created=now() - timedelta(days=7),
        )
        DateParticipantFactory.create(
            activity=fourth,
            created=now() - timedelta(days=5),
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)
        self.assertEqual(data['data'][0]['id'], str(fourth.pk))
        self.assertEqual(data['data'][1]['id'], str(third.pk))
        self.assertEqual(data['data'][2]['id'], str(second.pk))
        self.assertEqual(data['data'][3]['id'], str(first.pk))

    def test_sort_matching_status(self):
        DateActivityFactory.create(status='closed')
        second = DateActivityFactory.create(status='succeeded')
        DateParticipantFactory.create(activity=second)
        third = DateActivityFactory.create(
            status='open',
            capacity=1
        )
        DateParticipantFactory.create(activity=third)
        fourth = DateActivityFactory.create(status='running')
        DateParticipantFactory.create(activity=fourth)
        fifth = DateActivityFactory.create(status='open')
        DateParticipantFactory.create(activity=fifth)

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], str(fifth.pk))
        self.assertEqual(data['data'][1]['id'], str(fourth.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))
        self.assertEqual(data['data'][3]['id'], str(second.pk))

    def test_sort_matching_skill(self):
        skill = SkillFactory.create()
        self.owner.skills.add(skill)
        self.owner.save()

        first = PeriodActivityFactory.create(status='full')
        PeriodParticipantFactory.create_batch(3, activity=first, status='accepted')

        second = PeriodActivityFactory.create(status='full', expertise=skill)
        PeriodParticipantFactory.create_batch(3, activity=second, status='accepted')

        third = PeriodActivityFactory.create(status='open')
        fourth = PeriodActivityFactory.create(status='open', expertise=skill)

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], str(fourth.pk))
        self.assertEqual(data['data'][1]['id'], str(third.pk))
        self.assertEqual(data['data'][2]['id'], str(second.pk))
        self.assertEqual(data['data'][3]['id'], str(first.pk))

    def test_sort_matching_theme(self):
        theme = ProjectThemeFactory.create()
        self.owner.favourite_themes.add(theme)
        self.owner.save()

        initiative = InitiativeFactory.create(theme=theme)

        first = DateActivityFactory.create(status='open', capacity=1)
        DateParticipantFactory.create(activity=first)
        second = DateActivityFactory.create(
            status='open',
            initiative=initiative,
            capacity=1
        )
        DateParticipantFactory.create(activity=second)
        third = DateActivityFactory.create(status='open')
        DateParticipantFactory.create(activity=third)
        fourth = DateActivityFactory.create(status='open', initiative=initiative)

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], str(fourth.pk))
        self.assertEqual(data['data'][1]['id'], str(third.pk))
        self.assertEqual(data['data'][2]['id'], str(second.pk))
        self.assertEqual(data['data'][3]['id'], str(first.pk))

    def test_sort_matching_location(self):
        PlaceFactory.create(content_object=self.owner, position='10.0, 20.0')

        first = PeriodActivityFactory.create(status='full')
        PeriodParticipantFactory.create_batch(3, activity=first, status='accepted')

        second = PeriodActivityFactory.create(
            status='full',
            is_online=False,
            location=GeolocationFactory.create(position=Point(20.0, 10))
        )
        PeriodParticipantFactory.create_batch(3, activity=second, status='accepted')

        third = PeriodActivityFactory.create(
            status='open',
            is_online=False,
        )
        fourth = PeriodActivityFactory.create(
            status='open',
            is_online=False,
            location=GeolocationFactory.create(position=Point(21.0, 9.0))
        )
        fifth = PeriodActivityFactory.create(
            is_online=False,
            status='open', location=GeolocationFactory.create(position=Point(20.0, 10.0))
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)

        self.assertEqual(data['data'][0]['id'], str(fifth.pk))
        self.assertEqual(data['data'][1]['id'], str(fourth.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))
        self.assertEqual(data['data'][3]['id'], str(second.pk))
        self.assertEqual(data['data'][4]['id'], str(first.pk))

    def test_filter_country(self):
        country1 = CountryFactory.create()
        country2 = CountryFactory.create()

        initiative1 = InitiativeFactory.create(place=GeolocationFactory.create(country=country1))
        initiative2 = InitiativeFactory.create(place=GeolocationFactory.create(country=country2))
        initiative3 = InitiativeFactory.create(place=GeolocationFactory.create(country=country1))
        initiative4 = InitiativeFactory.create(place=GeolocationFactory.create(country=country2))

        location1 = GeolocationFactory(country=country1)
        location2 = GeolocationFactory(country=country2)

        first = PeriodActivityFactory.create(status='full', initiative=initiative1, location=location1)
        PeriodParticipantFactory.create_batch(3, activity=first, status='accepted')

        second = PeriodActivityFactory.create(status='open', initiative=initiative3, location=location1)

        third = PeriodActivityFactory.create(status='full', initiative=initiative2, location=location2)
        PeriodParticipantFactory.create_batch(3, activity=third, status='accepted')

        PeriodActivityFactory.create(status='open', initiative=initiative4)

        response = self.client.get(
            self.url + '?sort=popularity&filter[country]={}'.format(country1.id),
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)

        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_sort_matching_office_location(self):
        self.owner.location = LocationFactory.create(position='10.0, 20.0')
        self.owner.save()

        first = PeriodActivityFactory.create(status='full')
        PeriodParticipantFactory.create_batch(3, activity=first, status='accepted')

        second = PeriodActivityFactory.create(
            status='full',
            is_online=False,
            location=GeolocationFactory.create(position=Point(20.0, 10.0))
        )
        PeriodParticipantFactory.create_batch(3, activity=second, status='accepted')

        third = PeriodActivityFactory.create(status='open')
        fourth = PeriodActivityFactory.create(
            status='open',
            is_online=False,
            location=GeolocationFactory.create(position=Point(21.0, 9.0))
        )
        fifth = PeriodActivityFactory.create(
            status='open',
            is_online=False,
            location=GeolocationFactory.create(position=Point(20.0, 10.0))
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)

        self.assertEqual(data['data'][0]['id'], str(fifth.pk))
        self.assertEqual(data['data'][1]['id'], str(fourth.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))
        self.assertEqual(data['data'][3]['id'], str(second.pk))
        self.assertEqual(data['data'][4]['id'], str(first.pk))

    def test_sort_matching_created(self):
        first = DateActivityFactory.create(
            status='open', created=now() - timedelta(days=7)
        )
        second = DateActivityFactory.create(
            status='open', created=now() - timedelta(days=5)
        )
        third = DateActivityFactory.create(status='open', created=now() - timedelta(days=1))

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)

        self.assertEqual(data['data'][0]['id'], str(third.pk))
        self.assertEqual(data['data'][1]['id'], str(second.pk))
        self.assertEqual(data['data'][2]['id'], str(first.pk))

    def test_sort_matching_combined(self):
        theme = ProjectThemeFactory.create()
        self.owner.favourite_themes.add(theme)

        skill = SkillFactory.create()
        self.owner.skills.add(skill)

        self.owner.location = LocationFactory.create(position='10.0, 20.0')
        self.owner.save()

        initiative = InitiativeFactory.create(theme=theme)

        first = DateActivityFactory.create(
            status='open',
            initiative=initiative,
            is_online=False
        )
        second = PeriodActivityFactory.create(
            status='open',
            location=GeolocationFactory.create(position=Point(21.0, 9.0)),
            initiative=initiative,
            is_online=False
        )
        third = PeriodActivityFactory.create(
            status='open',
            location=GeolocationFactory.create(position=Point(21.0, 9.0)),
            initiative=initiative,
            expertise=skill,
            is_online=False
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)

        self.assertEqual(data['data'][0]['id'], str(third.pk))
        self.assertEqual(data['data'][1]['id'], str(second.pk))
        self.assertEqual(data['data'][2]['id'], str(first.pk))

    def test_limits(self):
        initiative = InitiativeFactory.create()
        DateActivityFactory.create_batch(
            7,
            status='open',
            initiative=initiative,
        )
        response = self.client.get(
            self.url + '?page[size]=150',
            user=self.owner
        )
        self.assertEqual(len(response.json()['data']), 7)

        response = self.client.get(
            self.url + '?page[size]=3',
            user=self.owner
        )
        self.assertEqual(len(response.json()['data']), 3)


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


class ContributorListAPITestCase(BluebottleTestCase):
    def setUp(self):
        super(ContributorListAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create()

        DateParticipantFactory.create_batch(2, user=self.user)
        PeriodParticipantFactory.create_batch(2, user=self.user)
        DonorFactory.create_batch(2, user=self.user, status='succeeded')
        DonorFactory.create_batch(2, user=self.user, status='new')

        DateParticipantFactory.create()
        PeriodParticipantFactory.create()
        DonorFactory.create()

        self.url = reverse('contributor-list')

    def test_get(self):
        response = self.client.get(
            self.url,
            user=self.user
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data['data']), 6)

        for contributor in data['data']:
            self.assertTrue(
                contributor['type'] in (
                    'contributors/time-based/date-participants',
                    'contributors/time-based/period-participants',
                    'contributors/donations',
                )
            )
            self.assertTrue(
                contributor['relationships']['activity']['data']['type'] in (
                    'activities/fundings',
                    'activities/time-based/dates',
                    'activities/time-based/periods'
                )
            )

            if contributor['type'] in (
                'activities/time-based/date-participant',
                'activities/time-based/period-participant',
            ):
                self.assertTrue('total-duration' in contributor['attributes'])

        for i in data['included']:
            if i['type'] == 'activities/time-based/date':
                self.assertTrue('start' in i['attributes'])
                self.assertTrue('duration' in i['attributes'])
                self.assertTrue('slug' in i['attributes'])
                self.assertTrue('title' in i['attributes'])

            if i['type'] == 'activities/time-based/period':
                self.assertTrue('deadline' in i['attributes'])
                self.assertTrue('duration-type' in i['attributes'])
                self.assertTrue('duration' in i['attributes'])
                self.assertTrue('slug' in i['attributes'])
                self.assertTrue('title' in i['attributes'])

            if i['type'] == 'activities/funding':
                self.assertTrue('slug' in i['attributes'])
                self.assertTrue('title' in i['attributes'])

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
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class ActivityAPIAnonymizationTestCase(ESTestCase, BluebottleTestCase):
    def setUp(self):
        super(ActivityAPIAnonymizationTestCase, self).setUp()
        self.member_settings = MemberPlatformSettings.load()

        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        last_year = now() - timedelta(days=400)
        self.old_date_activity = DateActivityFactory.create(
            created=last_year,
            status='open'
        )
        DateParticipantFactory.create(
            activity=self.old_date_activity,
            created=last_year
        )
        DateParticipantFactory.create(
            activity=self.old_date_activity
        )

        self.new_date_activity = DateActivityFactory.create(
            status='open'
        )
        DateParticipantFactory.create(
            activity=self.new_date_activity,
            created=last_year
        )
        DateParticipantFactory.create(
            activity=self.new_date_activity
        )
        self.new_url = reverse('date-detail', args=(self.new_date_activity.id,))
        self.old_url = reverse('date-detail', args=(self.old_date_activity.id,))

    def _get_members(self, data):
        return [item for item in data['included'] if item['type'] == 'members' and item['attributes']['first-name']]

    def _get_anonymous(self, data):
        return [item for item in data['included'] if item['type'] == 'members' and item['attributes']['is-anonymous']]

    def test_no_max_age(self):
        response = self.client.get(self.old_url, user=self.owner)
        data = json.loads(response.content)
        members = self._get_members(data)
        anonymous = self._get_anonymous(data)
        self.assertEqual(len(members), 2)
        self.assertEqual(len(anonymous), 0)

        contributors_response = self.client.get(
            data['data']['relationships']['contributors']['links']['related'], user=self.owner
        )
        contributors_data = json.loads(contributors_response.content)
        members = self._get_members(contributors_data)
        anonymous = self._get_anonymous(contributors_data)
        self.assertEqual(len(members), 2)
        self.assertEqual(len(anonymous), 0)

        response = self.client.get(self.new_url, user=self.owner)
        data = json.loads(response.content)
        members = self._get_members(data)
        anonymous = self._get_anonymous(data)
        self.assertEqual(len(members), 2)
        self.assertEqual(len(anonymous), 0)

        contributors_response = self.client.get(
            data['data']['relationships']['contributors']['links']['related'], user=self.owner
        )
        contributors_data = json.loads(contributors_response.content)
        members = self._get_members(contributors_data)
        anonymous = self._get_anonymous(contributors_data)
        self.assertEqual(len(members), 2)
        self.assertEqual(len(anonymous), 0)

    def test_max_age(self):
        self.member_settings.anonymization_age = 300
        self.member_settings.save()
        response = self.client.get(self.old_url, user=self.owner)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        members = self._get_members(data)
        anonymous = self._get_anonymous(data)
        self.assertEqual(len(members), 1)
        self.assertEqual(len(anonymous), 1)

        contributors_response = self.client.get(
            data['data']['relationships']['contributors']['links']['related'], user=self.owner
        )
        contributors_data = json.loads(contributors_response.content)
        members = self._get_members(contributors_data)
        anonymous = self._get_anonymous(contributors_data)
        self.assertEqual(len(members), 1)
        self.assertEqual(len(anonymous), 1)

        response = self.client.get(self.new_url, user=self.owner)
        data = json.loads(response.content)
        members = self._get_members(data)
        anonymous = self._get_anonymous(data)
        self.assertEqual(len(members), 2)
        self.assertEqual(len(anonymous), 0)

        contributors_response = self.client.get(
            data['data']['relationships']['contributors']['links']['related'], user=self.owner
        )
        contributors_data = json.loads(contributors_response.content)
        members = self._get_members(contributors_data)
        anonymous = self._get_anonymous(contributors_data)
        self.assertEqual(len(members), 1)
        self.assertEqual(len(anonymous), 1)
