import datetime
import json
from builtins import str

from django.contrib.auth.models import Group, Permission
from django.contrib.gis.geos import Point
from django.test import TestCase, tag
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import get_current_timezone, now
from django_elasticsearch_dsl.test import ESTestCase
from moneyed import Money
from rest_framework import status

from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.models import Theme
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.tests.factories import SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory, LocationFactory, CountryFactory
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.utils import JSONAPITestClient, BluebottleTestCase, APITestCase
from bluebottle.time_based.tests.factories import (
    PeriodActivityFactory, DateActivityFactory, PeriodParticipantFactory, DateParticipantFactory,
    DateActivitySlotFactory
)


def get_include(response, name):
    included = response.json()['included']
    return [include for include in included if include['type'] == name][0]


class InitiativeAPITestCase(TestCase):
    """
    Integration tests for the Categories API.
    """

    def setUp(self):
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        self.visitor = BlueBottleUserFactory.create()


class InitiativeListAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeListAPITestCase, self).setUp()
        self.theme = ThemeFactory.create()
        self.url = reverse('initiative-list')

    def test_create(self):
        data = {
            'data': {
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                },
                'relationships': {
                    'theme': {
                        'data': {
                            'type': 'themes',
                            'id': self.theme.pk
                        },
                    }
                }
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data),
            user=self.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = json.loads(response.content)

        initiative = Initiative.objects.get(pk=response_data['data']['id'])

        self.assertEqual(response_data['data']['attributes']['title'], 'Some title')
        self.assertEqual(response_data['data']['attributes']['slug'], 'some-title')
        self.assertEqual(initiative.title, 'Some title')
        self.assertEqual(
            response_data['data']['relationships']['owner']['data']['id'],
            str(self.owner.pk)
        )
        self.assertEqual(
            response_data['data']['relationships']['theme']['data']['id'],
            str(initiative.theme.pk)
        )
        self.assertEqual(len(response_data['included']), 2)

    def test_create_special_chars(self):
        data = {
            'data': {
                'type': 'initiatives',
                'attributes': {
                    'title': ':)'
                },
                'relationships': {
                    'theme': {
                        'data': {
                            'type': 'themes',
                            'id': self.theme.pk
                        },
                    }
                }
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data),
            user=self.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['data']['attributes']['title'], ':)')
        self.assertNotEqual(response_data['data']['attributes']['slug'], '')

    def test_create_missing_iamge(self):
        data = {
            'data': {
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                },
                'relationships': {
                    'theme': {
                        'data': {
                            'type': 'themes',
                            'id': self.theme.pk
                        },
                    }
                }
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data),
            user=self.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            '/data/attributes/image' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )

    def test_create_duplicate_title(self):
        InitiativeFactory.create(title='Some title', status='approved')
        data = {
            'data': {
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                },
                'relationships': {
                    'theme': {
                        'data': {
                            'type': 'themes',
                            'id': self.theme.pk
                        },
                    }
                }
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data),
            user=self.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertTrue(
            '/data/attributes/title' in (error['source']['pointer'] for error in data['data']['meta']['errors'])
        )

    def test_create_with_location(self):
        geolocation = GeolocationFactory.create(position=Point(23.6851594, 43.0579025))
        data = {
            'data': {
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                },
                'relationships': {
                    'place': {
                        'data': {
                            'type': 'geolocations',
                            'id': geolocation.id
                        },
                    }
                }
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data),
            user=self.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        geolocation = get_include(response, 'geolocations')
        self.assertEqual(geolocation['attributes']['position'],
                         {'latitude': 43.0579025, 'longitude': 23.6851594})

    def test_create_anonymous(self):
        response = self.client.post(
            self.url,
            json.dumps({})
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class InitiativeDetailAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeDetailAPITestCase, self).setUp()
        self.initiative = InitiativeFactory(
            owner=self.owner,
            place=GeolocationFactory(position=Point(23.6851594, 43.0579025))
        )
        self.initiative.states.submit(save=True)
        self.url = reverse('initiative-detail', args=(self.initiative.pk,))

        self.data = {
            'data': {
                'id': self.initiative.id,
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                }
            }
        }

    def test_patch(self):
        response = self.client.patch(
            self.url,
            json.dumps(self.data),
            user=self.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['title'], 'Some title')

    def test_patch_activity_manager(self):
        manager = BlueBottleUserFactory.create()
        self.initiative.activity_managers.add(manager)
        response = self.client.patch(
            self.url,
            json.dumps(self.data),
            user=manager
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['data']['attributes']['title'], 'Some title')

    def test_put_image(self):
        file_path = './bluebottle/files/tests/files/test-image.png'
        with open(file_path, 'rb') as test_file:
            response = self.client.post(
                reverse('image-list'),
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="some_file.png"',
                user=self.owner
            )

        file_data = json.loads(response.content)
        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'initiatives',
                'relationships': {
                    'image': {
                        'data': {
                            'type': 'images',
                            'id': file_data['data']['id']
                        }
                    }
                }
            }
        }
        response = self.client.patch(
            self.url,
            json.dumps(data),
            content_type="application/vnd.api+json",
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(
            data['data']['relationships']['image']['data']['id'],
            file_data['data']['id']
        )

        image = get_include(response, 'images')
        response = self.client.get(
            image['attributes']['links']['large'],
            user=self.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response['X-Accel-Redirect'].startswith(
                '/media/cache/'
            )
        )

    def test_patch_anonymous(self):
        response = self.client.patch(
            self.url,
            json.dumps(self.data),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_wrong_user(self):
        response = self.client.patch(
            self.url,
            json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_cancelled(self):
        self.initiative.states.approve()
        self.initiative.states.cancel(save=True)
        response = self.client.put(self.url, json.dumps(self.data), user=self.initiative.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_deleted(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.delete(save=True)
        response = self.client.put(self.url, json.dumps(self.data), user=self.initiative.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_rejected(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.reject(save=True)
        response = self.client.put(self.url, json.dumps(self.data), user=self.initiative.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_owner(self):
        self.initiative.title = ''
        self.initiative.save()

        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.initiative.title)
        self.assertEqual(data['meta']['status'], self.initiative.status)
        self.assertEqual(
            data['meta']['transitions'],
            [{
                u'available': True,
                u'name': u'request_changes',
                u'target': u'needs_work'
            }])
        self.assertEqual(data['relationships']['theme']['data']['id'], str(self.initiative.theme.pk))
        self.assertEqual(data['relationships']['owner']['data']['id'], str(self.initiative.owner.pk))

        geolocation = get_include(response, 'geolocations')
        self.assertEqual(geolocation['attributes']['position'], {'latitude': 43.0579025, 'longitude': 23.6851594})

        self.assertTrue(
            '/data/attributes/title' in (error['source']['pointer'] for error in data['meta']['required'])
        )

    def test_get_image_used_twice(self):
        InitiativeFactory.create(image=self.initiative.image)

        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['attributes']['title'], self.initiative.title)

    def test_get_no_image(self):
        self.initiative.image = None
        self.initiative.save()

        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['attributes']['title'], self.initiative.title)

    def test_get_activities(self):
        event = DateActivityFactory.create(
            status='full',
            initiative=self.initiative,
            image=ImageFactory.create(),
            slots=[]
        )

        DateActivityFactory.create(
            status='deleted',
            initiative=self.initiative,
        )
        DateActivityFactory.create(
            status='cancelled',
            initiative=self.initiative,
        )

        funding = FundingFactory.create(
            status='partially_funded',
            initiative=self.initiative
        )
        DateActivitySlotFactory.create(activity=event)
        response = self.client.get(self.url)

        data = response.json()['data']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 2)
        activity_types = [rel['type'] for rel in data['relationships']['activities']['data']]

        self.assertTrue(
            'activities/fundings' in activity_types
        )
        self.assertTrue(
            'activities/time-based/dates' in activity_types
        )

        event_data = get_include(response, 'activities/time-based/dates')
        self.assertEqual(event_data['id'], str(event.pk))
        self.assertEqual(
            event_data['attributes']['title'],
            event.title
        )

        funding_data = get_include(response, 'activities/fundings')
        self.assertEqual(funding_data['id'], str(funding.pk))
        self.assertEqual(
            funding_data['attributes']['title'],
            funding.title
        )

        activity_image = event_data['relationships']['image']['data']

        self.assertTrue(
            activity_image in (
                {'type': included['type'], 'id': included['id']} for included in
                response.json()['included']
            )
        )

    def test_get_activities_owner(self):
        DateActivityFactory.create(
            status='full',
            initiative=self.initiative,
        )

        DateActivityFactory.create(
            status='cancelled',
            initiative=self.initiative,
        )

        DateActivityFactory.create(
            status='deleted',
            initiative=self.initiative,
        )

        FundingFactory.create(
            status='partially_funded',
            initiative=self.initiative
        )
        response = self.client.get(self.url, user=self.initiative.owner)

        data = response.json()['data']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 3)

    def test_get_activities_managers(self):
        DateActivityFactory.create(
            status='draft',
            initiative=self.initiative,
        )

        DateActivityFactory.create(
            status='cancelled',
            initiative=self.initiative,
        )

        DateActivityFactory.create(
            status='deleted',
            initiative=self.initiative,
        )

        FundingFactory.create(
            status='partially_funded',
            initiative=self.initiative
        )
        manager = BlueBottleUserFactory.create()
        self.initiative.activity_managers.add(manager)
        response = self.client.get(self.url, user=manager)

        data = response.json()['data']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 3)

    def test_get_activities_closed_segments(self):
        open_segment = SegmentFactory.create(closed=False)
        closed_segment = SegmentFactory.create(closed=True)
        user = BlueBottleUserFactory.create()
        user.segments.add(closed_segment)
        another_user = BlueBottleUserFactory.create()
        another_user.segments.add(open_segment)
        staff_member = BlueBottleUserFactory.create(is_staff=True)

        act1 = DateActivityFactory.create(
            status='open',
            initiative=self.initiative,
        )
        act1.segments.add(open_segment)

        act2 = DateActivityFactory.create(
            status='open',
            initiative=self.initiative,
        )
        act2.segments.add(closed_segment)

        act3 = DateActivityFactory.create(
            status='open',
            initiative=self.initiative,
        )
        act3.segments.add(closed_segment)
        act3.segments.add(open_segment)
        response = self.client.get(self.url, user=user)
        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 3)
        response = self.client.get(self.url, user=another_user)
        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 1)
        response = self.client.get(self.url)
        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 1)
        response = self.client.get(self.url, user=staff_member)
        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 3)

    def test_deleted_activities(self):
        DateActivityFactory.create(initiative=self.initiative, status='deleted')
        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 0)

    def test_get_stats(self):
        self.initiative.states.approve(save=True)

        period_activity = PeriodActivityFactory.create(
            initiative=self.initiative,
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() - datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )

        period_activity.states.submit(save=True)
        PeriodParticipantFactory.create_batch(3, activity=period_activity)
        PeriodParticipantFactory.create_batch(3, activity=period_activity, status='withdrawn')

        date_activity = DateActivityFactory.create(
            initiative=self.initiative,
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=2)

        )
        date_activity.states.submit(save=True)
        DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() - datetime.timedelta(weeks=1),
        )
        DateParticipantFactory.create_batch(3, activity=date_activity)
        DateParticipantFactory.create_batch(3, activity=date_activity, status='withdrawn')

        funding = FundingFactory.create(
            initiative=self.initiative,
            deadline=now() - datetime.timedelta(weeks=1),
            status='succeeded'
        )
        donor_user = BlueBottleUserFactory.create()
        for donor in DonorFactory.create_batch(3, activity=funding, user=donor_user, amount=Money(10, 'EUR')):
            donor.contributions.get().states.succeed(save=True)
        for donor in DonorFactory.create_batch(3, activity=funding, user=None, amount=Money(10, 'USD')):
            donor.contributions.get().states.succeed(save=True)

        deed_activity = DeedFactory.create(
            initiative=self.initiative,
            start=datetime.date.today() - datetime.timedelta(days=10),
            end=datetime.date.today() - datetime.timedelta(days=5)
        )
        deed_activity.states.submit(save=True)
        deed_activity.states.succeed(save=True)

        DeedParticipantFactory.create_batch(3, activity=deed_activity)
        participants = DeedParticipantFactory.create_batch(3, activity=deed_activity)
        for participant in participants:
            participant.states.withdraw(save=True)

        collect_activity = CollectActivityFactory.create(
            initiative=self.initiative,
            start=datetime.date.today() - datetime.timedelta(weeks=2),
        )
        collect_activity.realized = 100
        collect_activity.states.submit(save=True)

        CollectContributorFactory.create_batch(3, activity=collect_activity)
        CollectContributorFactory.create_batch(3, activity=collect_activity, status='withdrawn')

        other_collect_activity = CollectActivityFactory.create(
            initiative=self.initiative,
            start=datetime.date.today() - datetime.timedelta(weeks=2),
        )
        other_collect_activity.realized = 200
        other_collect_activity.states.submit(save=True)

        CollectContributorFactory.create_batch(3, activity=other_collect_activity)

        # make an activity
        unrelated_initiative = InitiativeFactory.create()
        unrelated_initiative.states.submit()
        unrelated_initiative.states.approve(save=True)
        unrelated_activity = PeriodActivityFactory.create(
            initiative=unrelated_initiative,
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() - datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )

        unrelated_activity.states.submit(save=True)
        PeriodParticipantFactory.create_batch(3, activity=unrelated_activity)

        response = self.client.get(
            self.url,
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.json()['data']['meta']['stats']
        self.assertEqual(stats['hours'], 66.0)
        self.assertEqual(stats['activities'], 6)
        self.assertEqual(stats['amount'], {'amount': 75.0, 'currency': 'EUR'})

        # 3 period participants
        # 3 date participants
        # 1 donor (3 donations by same user)
        # 3 anonymous donations
        # 3 deed participants
        # 6 collect contributors
        # 19 total contributors
        # 3 withdrawn collect contributors not counted
        # organizers are not counted here
        self.assertEqual(stats['contributors'], 19)
        self.assertEqual(stats['effort'], 3)

        self.assertEqual(
            stats['collected'][str(collect_activity.collect_type_id)], collect_activity.realized
        )
        self.assertEqual(
            stats['collected'][str(other_collect_activity.collect_type_id)],
            other_collect_activity.realized
        )

    def test_get_other(self):
        response = self.client.get(
            self.url,
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.initiative.title)

    def test_get_anonymous(self):
        response = self.client.get(
            self.url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.initiative.title)


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class InitiativeListSearchAPITestCase(ESTestCase, InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeListSearchAPITestCase, self).setUp()
        self.url = reverse('initiative-list')

    def test_no_filter(self):
        InitiativeFactory.create(owner=self.owner, status='approved')
        InitiativeFactory.create(status='approved')

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)

    def test_more_results(self):
        InitiativeFactory.create_batch(19, owner=self.owner, status='approved')
        InitiativeFactory.create(status="approved")

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 20)
        self.assertEqual(len(data['data']), 8)

    def test_only_owner_permission(self):
        owned = InitiativeFactory.create(owner=self.owner, status='approved')
        InitiativeFactory.create(status="approved")

        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_initiative')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_initiative')
        )

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(len(data['data']), 1)

        self.assertEqual(data['data'][0]['id'], str(owned.pk))

    def test_only_owner_permission_owner(self):
        owned = InitiativeFactory.create(owner=self.owner, status='draft')
        InitiativeFactory.create(status="approved")

        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_initiative')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_initiative')
        )

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(len(data['data']), 1)

        self.assertEqual(data['data'][0]['id'], str(owned.pk))

    def test_not_approved(self):
        approved = InitiativeFactory.create(owner=self.owner, status='approved')
        InitiativeFactory.create(owner=self.owner)

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(approved.pk))

    def test_filter_segment(self):
        segment = SegmentFactory.create()

        first = InitiativeFactory.create(
            status='approved'
        )
        activity = DateActivityFactory.create(
            status='open',
            initiative=first,
        )
        activity.segments.add(segment)

        InitiativeFactory.create(
            status='approved'
        )

        response = self.client.get(
            self.url + '?filter[segment.{}]={}'.format(
                segment.segment_type.slug, segment.pk
            ),
            user=self.owner
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(first.pk))

    def test_filter_owner(self):
        owned_initiatives = InitiativeFactory.create_batch(
            2, status='submitted', owner=self.owner
        )

        managed_initiatives = InitiativeFactory.create_batch(
            2, status='submitted', activity_managers=[self.owner]
        )
        InitiativeFactory.create_batch(4, status='submitted')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)
        expected_ids = [str(initiative.pk) for initiative in owned_initiatives + managed_initiatives]

        for resource in data['data']:
            self.assertTrue(
                resource['id'] in expected_ids
            )

    def test_filter_owner_activity(self):
        InitiativeFactory.create_batch(4, status='submitted')

        with_activity = InitiativeFactory.create(status='submitted', owner=self.owner)
        activity = DateActivityFactory.create(owner=self.owner, initiative=with_activity)

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['relationships']['activities']['data'][0]['id'], str(activity.pk))

    def test_filter_country(self):
        mordor = CountryFactory.create(name='Mordor')
        location = LocationFactory.create(country=mordor)
        initiative = InitiativeFactory.create(status='approved', place=None, location=location)
        InitiativeFactory.create(status='approved', place=None)

        response = self.client.get(
            self.url + '?filter[country]={}'.format(mordor.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(initiative.pk))

    def test_filter_location(self):
        location = LocationFactory.create()
        initiative = InitiativeFactory.create(status='approved')
        DateActivityFactory.create(
            initiative=initiative,
            office_location=location,
            status='open'
        )
        InitiativeFactory.create(status='approved')

        response = self.client.get(
            self.url + '?filter[location.id]={}'.format(location.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['id'], str(initiative.pk))

    def test_filter_not_owner(self):
        """
        Non-owner should only see approved initiatives
        """
        InitiativeFactory.create_batch(2, status='submitted', owner=self.owner)
        InitiativeFactory.create_batch(4, status='approved', owner=self.owner)
        InitiativeFactory.create_batch(3, status='approved')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            user=self.visitor
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 4)
        self.assertEqual(data['data'][0]['relationships']['owner']['data']['id'], str(self.owner.pk))

    def test_filter_activity_manager(self):
        """
        User should see initiatives where self activity manager when in submitted
        """
        InitiativeFactory.create_batch(2, status='submitted', activity_managers=[self.owner])
        InitiativeFactory.create_batch(4, status='approved')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['relationships']['activity-managers']['data'][0]['id'], str(self.owner.pk))

    def test_filter_promoter(self):
        """
        User should see initiatives where self activity manager when in submitted
        """
        InitiativeFactory.create_batch(2, status='submitted', promoter=self.owner)
        InitiativeFactory.create_batch(4, status='approved')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)

    def test_filter_owner_and_activity_manager(self):
        """
        User should see initiatives where self owner or activity manager when in submitted
        """
        InitiativeFactory.create_batch(2, status='submitted', activity_managers=[self.owner])
        InitiativeFactory.create_batch(3, status='submitted', owner=self.owner)
        InitiativeFactory.create_batch(4, status='approved')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)

    def test_search(self):
        first = InitiativeFactory.create(title='Lorem ipsum dolor sit amet', pitch="Lorem ipsum", status='approved')
        InitiativeFactory.create(title='consectetur adipiscing elit', status='approved')
        InitiativeFactory.create(title='Nam eu turpis erat', status='approved')
        second = InitiativeFactory.create(title='Lorem ipsum dolor sit amet', status='approved')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_search_boost(self):
        first = InitiativeFactory.create(title='Something else', pitch='Lorem ipsum dolor sit amet', status='approved')
        second = InitiativeFactory.create(title='Lorem ipsum dolor sit amet', pitch="Something else", status='approved')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_search_location(self):
        location = LocationFactory.create(name='nameofoffice')
        first = InitiativeFactory.create(status='approved')
        second = InitiativeFactory.create(status='approved', title='nameofoffice')

        DateActivityFactory.create(
            initiative=first,
            office_location=location,
            status='open'
        )

        InitiativeFactory.create(status='approved')

        response = self.client.get(
            self.url + '?filter[search]=nameofoffice',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], str(second.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))

    def test_sort_title(self):
        second = InitiativeFactory.create(title='B: something else', status='approved')
        third = InitiativeFactory.create(title='C: More', status='approved')
        first = InitiativeFactory.create(title='A: something', status='approved')

        response = self.client.get(
            self.url + '?sort=alphabetical',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)
        self.assertEqual(data['data'][0]['id'], str(first.pk))
        self.assertEqual(data['data'][1]['id'], str(second.pk))
        self.assertEqual(data['data'][2]['id'], str(third.pk))

    def test_sort_created(self):
        first = InitiativeFactory.create(status='approved')
        second = InitiativeFactory.create(status='approved')
        third = InitiativeFactory.create(status='approved')

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
        self.assertEqual(data['data'][0]['id'], str(third.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))
        self.assertEqual(data['data'][2]['id'], str(second.pk))

    def test_sort_activity_date(self):
        first = InitiativeFactory.create(status='approved')
        FundingFactory.create(
            initiative=first,
            status='open',
            deadline=now() + datetime.timedelta(days=8)
        )
        FundingFactory.create(
            initiative=first,
            status='submitted',
            deadline=now() + datetime.timedelta(days=7)
        )

        second = InitiativeFactory.create(status='approved')
        activity = DateActivityFactory.create(
            initiative=second,
            status='open',
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=activity,
            start=now() + datetime.timedelta(days=7)
        )
        third = InitiativeFactory.create(status='approved')
        activity = DateActivityFactory.create(
            initiative=third,
            status='open',
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=activity,
            start=now() + datetime.timedelta(days=6)
        )
        PeriodActivityFactory.create(
            initiative=third,
            status='open',
            deadline=(now() + datetime.timedelta(days=9)).date()
        )

        fourth = InitiativeFactory.create(status='approved')
        PeriodActivityFactory.create(
            initiative=fourth,
            status='succeeded',
            deadline=(now() + datetime.timedelta(days=7)).date()
        )

        fifth = InitiativeFactory.create(status='approved')
        PeriodActivityFactory.create(
            initiative=fourth,
            status='succeeded',
            deadline=(now() + datetime.timedelta(days=8)).date()
        )

        response = self.client.get(
            self.url + '?sort=activity_date',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 5)
        self.assertEqual(data['data'][0]['id'], str(third.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))
        self.assertEqual(data['data'][2]['id'], str(second.pk))
        self.assertEqual(data['data'][3]['id'], str(fourth.pk))
        self.assertEqual(data['data'][4]['id'], str(fifth.pk))


class InitiativeReviewTransitionListAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeReviewTransitionListAPITestCase, self).setUp()

        self.url = reverse('initiative-review-transition-list')

        self.initiative = InitiativeFactory(
            has_organization=False,
            owner=self.owner
        )

    def test_transition_disallowed(self):
        self.initiative.states.submit(save=True)

        data = {
            'data': {
                'type': 'initiative-transitions',
                'attributes': {
                    'transition': 'approve',
                },
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'initiatives',
                            'id': self.initiative.pk
                        }
                    }
                }
            }
        }

        response = self.client.post(
            self.url,
            json.dumps(data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], u'Transition is not available')

        initiative = Initiative.objects.get(pk=self.initiative.pk)
        self.assertEqual(initiative.status, 'submitted')


class InitiativeRedirectTest(TestCase):
    def setUp(self):
        super(InitiativeRedirectTest, self).setUp()
        self.client = JSONAPITestClient()

        self.url = reverse('initiative-redirect-list')

    def test_initiative(self):
        initiative = InitiativeFactory.create()
        data = {
            'data': {
                'type': 'initiative-redirects',
                'attributes': {
                    'route': 'project',
                    'params': {'project_id': initiative.slug}
                },
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            response.json()['data']['attributes']['target-route'], 'initiatives.details'
        )

        self.assertEqual(
            response.json()['data']['attributes']['target-params'], [initiative.pk, initiative.slug]
        )

    def test_initiative_duplicate(self):
        initiative = InitiativeFactory.create()
        InitiativeFactory.create(slug=initiative.slug)

        data = {
            'data': {
                'type': 'initiative-redirects',
                'attributes': {
                    'route': 'project',
                    'params': {'project_id': initiative.slug}
                },
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            response.json()['data']['attributes']['target-route'], 'initiatives.details'
        )

        self.assertEqual(
            response.json()['data']['attributes']['target-params'], [initiative.pk, initiative.slug]
        )

    def test_initiative_with_funding(self):
        initiative = InitiativeFactory.create()
        funding = FundingFactory.create(initiative=initiative)

        data = {
            'data': {
                'type': 'initiative-redirects',
                'attributes': {
                    'route': 'project',
                    'params': {'project_id': initiative.slug}
                },
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            response.json()['data']['attributes']['target-route'], 'initiatives.activities.details.funding'
        )

        self.assertEqual(
            response.json()['data']['attributes']['target-params'], [funding.pk, funding.slug]
        )

    def test_does_not_exist(self):

        data = {
            'data': {
                'type': 'initiative-redirects',
                'attributes': {
                    'route': 'tasks.detail',
                    'params': {'id': '123'}
                },
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class InitiativeRelatedImageAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeRelatedImageAPITestCase, self).setUp()
        self.initiative = InitiativeFactory(
            owner=self.owner,
        )
        self.url = reverse('initiative-detail', args=(self.initiative.pk,))
        self.related_image_url = reverse('related-initiative-image-list')

        file_path = './bluebottle/files/tests/files/test-image.png'

        with open(file_path, 'rb') as test_file:
            response = self.client.post(
                reverse('image-list'),
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="some_file.jpg"',
                user=self.owner
            )

        self.file_data = json.loads(response.content)

    def test_create(self):
        data = {
            'data': {
                'type': 'related-initiative-images',
                'relationships': {
                    'image': {
                        'data': {
                            'type': 'images',
                            'id': self.file_data['data']['id']
                        }
                    },
                    'resource': {
                        'data': {
                            'type': 'initiatives',
                            'id': self.initiative.pk,
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
            response.json()['included'][0]['attributes']['links']['large'].split('?')[0],
            u'/api/initiatives/{}/related-image/600'.format(response.json()['data']['id'])
        )

    def test_create_non_owner(self):
        data = {
            'data': {
                'type': 'related-initiative-images',
                'relationships': {
                    'image': {
                        'data': {
                            'type': 'images',
                            'id': self.file_data['data']['id']
                        }
                    },
                    'resource': {
                        'data': {
                            'type': 'initiatives',
                            'id': self.initiative.pk,
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


class ThemeAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(ThemeAPITestCase, self).setUp()

        self.client = JSONAPITestClient()
        Theme.objects.all().delete()

        self.list_url = reverse('initiative-theme-list')
        self.user = BlueBottleUserFactory()
        themes = ThemeFactory.create_batch(5, disabled=False)
        self.theme = themes[0]
        self.detail_url = reverse('initiative-theme', args=(self.theme.id,))

    def test_list(self):
        response = self.client.get(self.list_url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )
        result = response.json()['data'][0]
        self.assertEqual(self.theme.name, result['attributes']['name'])

    def test_list_anonymous(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.json()['data']), 5
        )

    def test_list_closed(self):
        MemberPlatformSettings.objects.update(closed=True)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_disabled(self):
        ThemeFactory.create(disabled=True)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.json()['data']), 5
        )

    def test_detail(self):
        response = self.client.get(self.detail_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()['data']
        self.assertEqual(result['attributes']['name'], self.theme.name)

    def test_detail_anonymous(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()['data']
        self.assertEqual(result['attributes']['name'], self.theme.name)

    def test_detail_closed(self):
        MemberPlatformSettings.objects.update(closed=True)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_disabled(self):
        theme = ThemeFactory.create(disabled=True)
        url = reverse('initiative-theme', args=(theme.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ThemeApiTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        MemberPlatformSettings.objects.update(closed=True)
        self.url = reverse('initiative-theme-list')
        self.client = JSONAPITestClient()

    def test_get_skills_authenticated(self):
        user = BlueBottleUserFactory.create()
        response = self.client.get(self.url, user=user)
        self.assertEqual(response.status_code, 200)

    def test_get_skills_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


class InitiativeAPITestCase(APITestCase):

    def setUp(self):
        super().setUp()

        self.model = InitiativeFactory.create(
            status='approved'
        )
        self.url = reverse('initiative-detail', args=(self.model.id,))

    def test_get_with_segments(self):
        segment = SegmentFactory.create(
            name='SDG1'
        )
        activity = DateActivityFactory.create(
            initiative=self.model,
            status='open',
        )
        activity.segments.add(segment)

        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertRelationship('segments', [segment])
