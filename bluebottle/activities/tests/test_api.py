import datetime
import json

from django.contrib.auth.models import Group, Permission
from django.test import tag
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import get_current_timezone, now

from django.contrib.gis.geos import Point

from django_elasticsearch_dsl.test import ESTestCase

from rest_framework import status

from bluebottle.assignments.tests.factories import AssignmentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.funding.tests.factories import FundingFactory

from bluebottle.test.factory_models.geo import LocationFactory, GeolocationFactory, PlaceFactory, CountryFactory
from bluebottle.test.factory_models.tasks import SkillFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectThemeFactory
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

    def test_no_filter(self):
        succeeded = EventFactory.create(
            owner=self.owner, review_status='approved', status='succeeded'
        )
        open = EventFactory.create(review_status='approved', status='open')
        EventFactory.create(status='in_review')
        EventFactory.create(review_status='approved', status='closed')

        response = self.client.get(self.url, user=self.owner)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][1]['id'], unicode(succeeded.pk))
        self.assertEqual(data['data'][0]['id'], unicode(open.pk))

        self.assertTrue('meta' in data['data'][0])

    def test_anonymous(self):
        succeeded = EventFactory.create(
            owner=self.owner, review_status='approved', status='succeeded'
        )
        open = EventFactory.create(review_status='approved', status='open')
        EventFactory.create(status='in_review')
        EventFactory.create(review_status='approved', status='closed')

        response = self.client.get(self.url)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][1]['id'], unicode(succeeded.pk))
        self.assertEqual(data['data'][0]['id'], unicode(open.pk))

        self.assertTrue('meta' in data['data'][0])

    def test_filter_owner(self):
        EventFactory.create(owner=self.owner, review_status='approved')
        EventFactory.create(review_status='approved')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['relationships']['owner']['data']['id'], unicode(self.owner.pk))

    def test_only_owner_permission(self):
        EventFactory.create(owner=self.owner, review_status='approved')
        EventFactory.create(review_status='approved')

        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_activity')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_activity')
        )

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)

        self.assertEqual(data['data'][0]['relationships']['owner']['data']['id'], unicode(self.owner.pk))

    def test_initiative_location(self):
        location = LocationFactory.create()
        initiative = InitiativeFactory.create(status='approved', location=location)
        activity = EventFactory.create(review_status='approved', initiative=initiative)
        EventFactory.create(review_status='approved')

        response = self.client.get(
            self.url + '?filter[initiative_location.id]={}'.format(location.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], unicode(activity.pk))

    def test_deadline(self):
        event = EventFactory.create(
            review_status='approved',
            start_date=datetime.date(2019, 1, 14)
        )
        EventFactory.create(
            review_status='approved',
            start_date=datetime.date(2019, 4, 14)
        )
        date_assignment = AssignmentFactory.create(
            review_status='approved',
            end_date=datetime.date(2019, 1, 14),
            end_date_type='on_date'
        )
        AssignmentFactory.create(
            review_status='approved',
            end_date=datetime.date(2019, 4, 14),
            end_date_type='on_date'
        )
        deadline_assignment = AssignmentFactory.create(
            review_status='approved',
            end_date=datetime.date(2019, 4, 14),
            end_date_type='deadline'
        )
        FundingFactory.create(review_status='approved')

        response = self.client.get(
            self.url + '?filter[date]=2019-01-01',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 3)

        found = [item['id'] for item in data['data']]

        self.assertTrue(unicode(event.pk) in found)
        self.assertTrue(unicode(date_assignment.pk) in found)
        self.assertTrue(unicode(deadline_assignment.pk) in found)

    def test_search(self):
        first = EventFactory.create(
            title='Lorem ipsum dolor sit amet',
            description="Lorem ipsum",
            review_status='approved'
        )
        second = EventFactory.create(title='Lorem ipsum dolor sit amet', review_status='approved')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(first.pk))
        self.assertEqual(data['data'][1]['id'], unicode(second.pk))

    def test_search_different_type(self):
        first = EventFactory.create(
            title='Lorem ipsum dolor sit amet',
            description="Lorem ipsum",
            review_status='approved'
        )
        second = FundingFactory.create(title='Lorem ipsum dolor sit amet', review_status='approved')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(first.pk))
        self.assertEqual(data['data'][0]['type'], 'activities/events')
        self.assertEqual(data['data'][1]['id'], unicode(second.pk))
        self.assertEqual(data['data'][1]['type'], 'activities/fundings')

    def test_search_boost(self):
        first = EventFactory.create(
            title='Something else',
            description='Lorem ipsum dolor sit amet',
            review_status='approved'
        )
        second = EventFactory.create(
            title='Lorem ipsum dolor sit amet',
            description="Something else",
            review_status='approved'
        )

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(second.pk))
        self.assertEqual(data['data'][1]['id'], unicode(first.pk))

    def test_search_formatted_address(self):
        location = GeolocationFactory.create(formatted_address='Roggeveenstraat')
        first = EventFactory.create(
            location=location,
            review_status='approved'
        )
        second = EventFactory.create(
            title='Roggeveenstraat',
            review_status='approved'
        )
        EventFactory.create(
            review_status='approved'
        )

        response = self.client.get(
            self.url + '?filter[search]=Roggeveenstraat',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(second.pk))
        self.assertEqual(data['data'][1]['id'], unicode(first.pk))

    def test_search_initiative_title(self):
        first = EventFactory.create(
            initiative=InitiativeFactory.create(title='Test title'),
            review_status='approved'
        )
        second = EventFactory.create(
            title='Test title',
            review_status='approved'
        )
        EventFactory.create(
            review_status='approved'
        )

        response = self.client.get(
            self.url + '?filter[search]=test title',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(second.pk))
        self.assertEqual(data['data'][1]['id'], unicode(first.pk))

    def test_sort_title(self):
        second = EventFactory.create(title='B: something else', review_status='approved')
        first = EventFactory.create(title='A: something', review_status='approved')
        third = EventFactory.create(title='C: More', review_status='approved')

        response = self.client.get(
            self.url + '?sort=alphabetical',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)
        self.assertEqual(data['data'][0]['id'], unicode(first.pk))
        self.assertEqual(data['data'][1]['id'], unicode(second.pk))
        self.assertEqual(data['data'][2]['id'], unicode(third.pk))

    def test_sort_created(self):
        first = EventFactory.create(review_status='approved')
        second = EventFactory.create(review_status='approved')
        third = EventFactory.create(review_status='approved')

        first.created = datetime.datetime(2018, 5, 8, tzinfo=get_current_timezone())
        first.save()
        second.created = datetime.datetime(2018, 5, 7, tzinfo=get_current_timezone())
        second.save()
        third.created = datetime.datetime(2018, 5, 9, tzinfo=get_current_timezone())
        third.save()

        response = self.client.get(
            self.url + '?sort=date',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)
        self.assertEqual(data['data'][0]['id'], unicode(third.pk))
        self.assertEqual(data['data'][1]['id'], unicode(first.pk))
        self.assertEqual(data['data'][2]['id'], unicode(second.pk))

    def test_sort_matching_popularity(self):
        first = EventFactory.create(review_status='approved')
        second = EventFactory.create(review_status='approved')
        ParticipantFactory.create(
            activity=second, created=now() - datetime.timedelta(days=7)
        )

        third = EventFactory.create(review_status='approved')
        ParticipantFactory.create(
            activity=third, created=now() - datetime.timedelta(days=5)
        )

        fourth = EventFactory.create(review_status='approved')
        ParticipantFactory.create(
            activity=fourth, created=now() - datetime.timedelta(days=7)
        )
        ParticipantFactory.create(
            activity=fourth, created=now() - datetime.timedelta(days=5)
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], unicode(fourth.pk))
        self.assertEqual(data['data'][1]['id'], unicode(third.pk))
        self.assertEqual(data['data'][2]['id'], unicode(second.pk))
        self.assertEqual(data['data'][3]['id'], unicode(first.pk))

    def test_sort_matching_status(self):
        EventFactory.create(review_status='approved', status='closed')
        second = EventFactory.create(review_status='approved', status='succeeded')
        ParticipantFactory.create(activity=second)
        third = EventFactory.create(
            review_status='approved',
            status='open',
            capacity=1
        )
        ParticipantFactory.create(activity=third)
        fourth = EventFactory.create(review_status='approved', status='running')
        ParticipantFactory.create(activity=fourth)
        fifth = EventFactory.create(review_status='approved', status='open')
        ParticipantFactory.create(activity=fifth)

        response = self.client.get(
            self.url + '?sort=popularity',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], unicode(fifth.pk))
        self.assertEqual(data['data'][1]['id'], unicode(fourth.pk))
        self.assertEqual(data['data'][2]['id'], unicode(third.pk))
        self.assertEqual(data['data'][3]['id'], unicode(second.pk))

    def test_sort_matching_skill(self):
        skill = SkillFactory.create()
        self.owner.skills.add(skill)
        self.owner.save()

        first = AssignmentFactory.create(review_status='approved', status='full')
        second = AssignmentFactory.create(review_status='approved', status='full', expertise=skill)
        third = AssignmentFactory.create(review_status='approved', status='open')
        fourth = AssignmentFactory.create(review_status='approved', status='open', expertise=skill)

        response = self.client.get(
            self.url + '?sort=popularity',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], unicode(fourth.pk))
        self.assertEqual(data['data'][1]['id'], unicode(third.pk))
        self.assertEqual(data['data'][2]['id'], unicode(second.pk))
        self.assertEqual(data['data'][3]['id'], unicode(first.pk))

    def test_sort_matching_theme(self):
        theme = ProjectThemeFactory.create()
        self.owner.favourite_themes.add(theme)
        self.owner.save()

        initiative = InitiativeFactory.create(theme=theme)

        first = EventFactory.create(review_status='approved', status='open', capacity=1)
        ParticipantFactory.create(activity=first)
        second = EventFactory.create(
            review_status='approved',
            status='open',
            initiative=initiative,
            capacity=1
        )
        ParticipantFactory.create(activity=second)
        third = EventFactory.create(review_status='approved', status='open')
        ParticipantFactory.create(activity=third)
        fourth = EventFactory.create(review_status='approved', status='open', initiative=initiative)
        ParticipantFactory.create(activity=fourth)

        response = self.client.get(
            self.url + '?sort=popularity',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)

        self.assertEqual(data['data'][0]['id'], unicode(fourth.pk))
        self.assertEqual(data['data'][1]['id'], unicode(third.pk))
        self.assertEqual(data['data'][2]['id'], unicode(second.pk))
        self.assertEqual(data['data'][3]['id'], unicode(first.pk))

    def test_sort_matching_location(self):
        PlaceFactory.create(content_object=self.owner, position='10.0, 20.0')

        first = AssignmentFactory.create(review_status='approved', status='full')
        second = AssignmentFactory.create(
            review_status='approved',
            status='full',
            location=GeolocationFactory.create(position=Point(20.0, 10))
        )
        third = AssignmentFactory.create(review_status='approved', status='open')
        fourth = AssignmentFactory.create(
            review_status='approved',
            status='open',
            location=GeolocationFactory.create(position=Point(21.0, 9.0))
        )
        fifth = AssignmentFactory.create(
            review_status='approved',
            status='open', location=GeolocationFactory.create(position=Point(20.0, 10.0))
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)

        self.assertEqual(data['data'][0]['id'], unicode(fifth.pk))
        self.assertEqual(data['data'][1]['id'], unicode(fourth.pk))
        self.assertEqual(data['data'][2]['id'], unicode(third.pk))
        self.assertEqual(data['data'][3]['id'], unicode(second.pk))
        self.assertEqual(data['data'][4]['id'], unicode(first.pk))

    def test_filter_country(self):
        country1 = CountryFactory.create()
        country2 = CountryFactory.create()

        initiative1 = InitiativeFactory.create(place=GeolocationFactory.create(country=country1))
        initiative2 = InitiativeFactory.create(place=GeolocationFactory.create(country=country2))
        initiative3 = InitiativeFactory.create(place=GeolocationFactory.create(country=country1))
        initiative4 = InitiativeFactory.create(place=GeolocationFactory.create(country=country2))

        first = AssignmentFactory.create(review_status='approved', status='full', initiative=initiative1)
        second = AssignmentFactory.create(review_status='approved', status='open', initiative=initiative3)
        AssignmentFactory.create(review_status='approved', status='full', initiative=initiative2)
        AssignmentFactory.create(review_status='approved', status='open', initiative=initiative4)

        response = self.client.get(
            self.url + '?sort=popularity&filter[country]={}'.format(country1.id),
            user=self.owner
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)

        self.assertEqual(data['data'][0]['id'], unicode(second.pk))
        self.assertEqual(data['data'][1]['id'], unicode(first.pk))

    def test_sort_matching_office_location(self):
        self.owner.location = LocationFactory.create(position='10.0, 20.0')
        self.owner.save()

        first = AssignmentFactory.create(review_status='approved', status='full')
        second = AssignmentFactory.create(
            review_status='approved',
            status='full',
            location=GeolocationFactory.create(position=Point(20.0, 10.0))
        )
        third = AssignmentFactory.create(review_status='approved', status='open')
        fourth = AssignmentFactory.create(
            review_status='approved',
            status='open',
            location=GeolocationFactory.create(position=Point(21.0, 9.0))
        )
        fifth = AssignmentFactory.create(
            review_status='approved',
            status='open',
            location=GeolocationFactory.create(position=Point(20.0, 10.0))
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)

        self.assertEqual(data['data'][0]['id'], unicode(fifth.pk))
        self.assertEqual(data['data'][1]['id'], unicode(fourth.pk))
        self.assertEqual(data['data'][2]['id'], unicode(third.pk))
        self.assertEqual(data['data'][3]['id'], unicode(second.pk))
        self.assertEqual(data['data'][4]['id'], unicode(first.pk))

    def test_sort_matching_created(self):
        first = EventFactory.create(
            review_status='approved', status='open', created=now() - datetime.timedelta(days=7)
        )
        second = EventFactory.create(
            review_status='approved', status='open', created=now() - datetime.timedelta(days=5)
        )
        third = EventFactory.create(review_status='approved', status='open', created=now() - datetime.timedelta(days=1))

        response = self.client.get(
            self.url + '?sort=popularity',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)

        self.assertEqual(data['data'][0]['id'], unicode(third.pk))
        self.assertEqual(data['data'][1]['id'], unicode(second.pk))
        self.assertEqual(data['data'][2]['id'], unicode(first.pk))

    def test_sort_matching_combined(self):
        theme = ProjectThemeFactory.create()
        self.owner.favourite_themes.add(theme)

        skill = SkillFactory.create()
        self.owner.skills.add(skill)

        self.owner.location = LocationFactory.create(position='10.0, 20.0')
        self.owner.save()

        initiative = InitiativeFactory.create(theme=theme)

        first = EventFactory.create(review_status='approved', status='open', initiative=initiative)
        second = AssignmentFactory.create(
            review_status='approved',
            status='open',
            location=GeolocationFactory.create(position=Point(21.0, 9.0)),
            initiative=initiative,
        )
        third = AssignmentFactory.create(
            review_status='approved',
            status='open',
            location=GeolocationFactory.create(position=Point(21.0, 9.0)),
            initiative=initiative,
            expertise=skill
        )

        response = self.client.get(
            self.url + '?sort=popularity',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)

        self.assertEqual(data['data'][0]['id'], unicode(third.pk))
        self.assertEqual(data['data'][1]['id'], unicode(second.pk))
        self.assertEqual(data['data'][2]['id'], unicode(first.pk))


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

        with open(file_path) as test_file:
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
