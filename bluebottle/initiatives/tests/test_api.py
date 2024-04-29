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
from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.impact.models import ImpactType
from bluebottle.impact.tests.factories import ImpactGoalFactory
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings, InitiativeSearchFilter, \
    ActivitySearchFilter
from bluebottle.initiatives.models import Theme
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.categories import CategoryFactory
from bluebottle.test.factory_models.geo import GeolocationFactory, LocationFactory, CountryFactory
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.utils import JSONAPITestClient, BluebottleTestCase, APITestCase
from bluebottle.time_based.tests.factories import (
    DeadlineActivityFactory,
    DateActivityFactory,
    DeadlineParticipantFactory,
    DateParticipantFactory,
    DateActivitySlotFactory,
    SlotParticipantFactory,
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
        super().setUp()


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
                'available': True,
                'name': 'request_changes',
                'target': 'needs_work',
                'label': 'Needs work',
                'passed_label': None,
                'description': "The status of the initiative is set to 'Needs work'. The " +
                               "initiator can edit and resubmit the initiative. Don't forget " +
                               "to inform the initiator of the necessary adjustments."
            }])
        self.assertEqual(data['relationships']['theme']['data']['id'], str(self.initiative.theme.pk))
        self.assertEqual(data['relationships']['owner']['data']['id'], str(self.initiative.owner.pk))

        geolocation = get_include(response, 'geolocations')
        self.assertEqual(geolocation['attributes']['position'], {'latitude': 43.0579025, 'longitude': 23.6851594})

        self.assertTrue(
            '/data/attributes/title' in (error['source']['pointer'] for error in data['meta']['required'])
        )
        self.assertEqual(
            data['relationships']['activities']['links']['related'],
            f'/api/activities/search?filter[initiative.id]={self.initiative.id}&page[size]=1000'
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

    def test_get_stats(self):
        self.initiative.states.approve(save=True)

        period_activity = DeadlineActivityFactory.create(
            initiative=self.initiative,
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() - datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )

        period_activity.states.publish(save=True)
        DeadlineParticipantFactory.create_batch(3, activity=period_activity)
        DeadlineParticipantFactory.create_batch(
            3, activity=period_activity, status="withdrawn"
        )

        date_activity = DateActivityFactory.create(
            initiative=self.initiative,
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=2)

        )
        date_activity.states.publish(save=True)
        slot = DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() - datetime.timedelta(weeks=1),
        )
        for participant in DateParticipantFactory.create_batch(
            3, activity=date_activity
        ):
            SlotParticipantFactory.create(participant=participant, slot=slot)
        for participant in DateParticipantFactory.create_batch(
            3, activity=date_activity, status="rejected"
        ):
            SlotParticipantFactory.create(participant=participant, slot=slot)

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
        deed_activity.states.publish(save=True)
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
        unrelated_activity = DeadlineActivityFactory.create(
            initiative=unrelated_initiative,
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() - datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )

        unrelated_activity.states.publish(save=True)
        DeadlineParticipantFactory.create_batch(3, activity=unrelated_activity)

        response = self.client.get(
            self.url,
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.json()["data"]["meta"]["stats"]
        self.assertEqual(stats["hours"], 18.0)
        self.assertEqual(stats["activities"], 6)
        self.assertEqual(stats["amount"], {"amount": 75.0, "currency": "EUR"})

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

    def test_get_stats_impact(self):
        self.initiative.states.approve(save=True)

        co2 = ImpactType.objects.get(slug='co2')
        water = ImpactType.objects.get(slug='water')

        first = DeedFactory.create(
            initiative=self.initiative, target=5, enable_impact=True
        )
        ImpactGoalFactory.create(activity=first, type=co2, realized=100)
        ImpactGoalFactory.create(activity=first, type=water, realized=0, target=1000)
        DeedParticipantFactory.create_batch(5, activity=first)

        second = DeedFactory.create(
            initiative=self.initiative, target=5, enable_impact=True
        )
        ImpactGoalFactory.create(activity=second, type=co2, realized=200)
        ImpactGoalFactory.create(activity=second, type=water, realized=0, target=1000)

        third = DeedFactory.create(
            initiative=self.initiative, target=10, enable_impact=True
        )
        ImpactGoalFactory.create(activity=third, type=co2, realized=300)
        ImpactGoalFactory.create(activity=third, type=water, realized=0, target=500)
        DeedParticipantFactory.create_batch(5, activity=third)

        response = self.client.get(
            self.url,
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.json()['data']['meta']['stats']

        self.assertEqual(stats['impact'][0]['name'], 'reduce CO₂ emissions by {} kg')
        self.assertEqual(stats['impact'][0]['value'], 600.0)

        self.assertEqual(stats['impact'][1]['name'], 'water saved')
        self.assertEqual(stats['impact'][1]['value'], 1250.0)

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
class InitiativeListSearchAPITestCase(ESTestCase, BluebottleTestCase):
    def setUp(self):
        super(InitiativeListSearchAPITestCase, self).setUp()

        self.client = JSONAPITestClient()
        self.url = reverse('initiative-preview-list')
        self.owner = BlueBottleUserFactory.create()

    def search(self, filter, sort=None, user=None):
        if isinstance(filter, str):
            url = filter
        else:
            params = dict(
                (f'filter[{key}]', value) for key, value in filter.items()
            )

            if sort:
                params['sort'] = sort

            query = '&'.join(f'{key}={value}' for key, value in params.items())

            url = f'{self.url}?{query}'

        response = self.client.get(
            url,
            user=user
        )

        self.data = json.loads(response.content)

    def assertFound(self, matching, count=None):
        self.assertEqual(self.data['meta']['pagination']['count'], len(matching))

        if count:
            self.assertEqual(len(self.data['data']), count)

        ids = set(str(activity.pk) for activity in matching)

        for activity in self.data['data']:
            self.assertTrue(activity['id'] in ids)

    def assertFacets(self, filter, facets, active=None):
        found_facets = dict(
            (facet['id'], facet) for facet in self.data['meta']['facets'][filter]
        )

        for key, value in facets.items():
            self.assertEqual(found_facets[key]['count'], value)

        if active:
            self.assertTrue(found_facets[active]['active'])

    def test_no_filter(self):
        matching = (
            InitiativeFactory.create(owner=self.owner, status='approved'),
            InitiativeFactory.create(status='approved')
        )

        self.search({})
        self.assertFound(matching)

    def test_more_results(self):
        matching = InitiativeFactory.create_batch(20, status='approved')

        self.search({})

        self.assertFound(matching, 8)

    def test_only_owner(self):
        owned = InitiativeFactory.create(owner=self.owner, status='draft')
        InitiativeFactory.create(status="draft")

        response = self.client.get(
            self.url + '?filter[owner]=me',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(len(data['data']), 1)

        self.assertEqual(data['data'][0]['id'], str(owned.pk))

    def test_only_owner_as_guest(self):
        InitiativeFactory.create(status='approved')
        InitiativeFactory.create(status="draft")

        response = self.client.get(
            self.url + '?filter[owner]=me'
        )
        self.assertEqual(response.status_code, 401)

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
            self.url + '?filter[owner]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(len(data['data']), 1)

        self.assertEqual(data['data'][0]['id'], str(owned.pk))

    def test_filter_not_approved(self):
        matching = InitiativeFactory.create_batch(2, owner=self.owner, status='approved')
        other = InitiativeFactory.create_batch(3, owner=self.owner)

        self.search({}, user=self.owner)
        self.assertFound(matching)

        self.search({'owner': 'me'}, user=self.owner)
        self.assertFound(matching + other)

    def test_filter_owner(self):
        matching = (
            InitiativeFactory.create_batch(2, owner=self.owner, status='approved') +
            InitiativeFactory.create_batch(2, owner=self.owner, status='draft') +
            InitiativeFactory.create_batch(2, activity_managers=[self.owner], status='approved')
        )

        self.search({'owner': 'me'}, user=self.owner)
        self.assertFound(matching)

    def test_filter_segment(self):
        segment_type = SegmentTypeFactory.create()

        matching_segment, other_segment = SegmentFactory.create_batch(2, segment_type=segment_type)
        matching = InitiativeFactory.create_batch(3, status="approved")
        for initiative in matching:
            activity = DateActivityFactory.create(status='open', initiative=initiative)
            activity.segments.add(matching_segment)

        other = InitiativeFactory.create_batch(2, status="approved")
        for initiative in other:
            activity = DateActivityFactory.create(status='open', initiative=initiative)
            activity.segments.add(other_segment)

        self.search({f'segment.{segment_type.slug}': matching_segment.pk})

        self.assertFacets(
            f'segment.{segment_type.slug}',
            {
                str(f'{matching_segment.pk}'): len(matching),
                str(f'{other_segment.pk}'): len(other)
            }
        )
        self.assertFound(matching)

    def test_filter_country(self):
        matching_country, other_country = CountryFactory.create_batch(2)

        matching = InitiativeFactory.create_batch(2, status='approved')
        for initiative in matching:
            DeadlineActivityFactory.create(
                status='open',
                initiative=initiative,
                office_location=LocationFactory.create(country=matching_country)
            )

        other = InitiativeFactory.create_batch(3, status='approved')
        for initiative in other:
            DeadlineActivityFactory.create(
                status='open',
                initiative=initiative,
                office_location=LocationFactory.create(country=other_country)
            )

        self.search({'country': matching_country.pk})
        self.assertFacets(
            'country',
            {
                str(matching_country.pk): len(matching),
                str(other_country.pk): len(other)
            }
        )
        self.assertFound(matching)

    def test_filter_office(self):
        settings, _ = InitiativePlatformSettings.objects.get_or_create()
        settings.search_filters_initiatives.add(
            InitiativeSearchFilter.objects.create(
                settings=settings,
                type='office'
            )
        )

        matching_office = LocationFactory.create()

        matching = InitiativeFactory.create_batch(2, status='approved')
        for initiative in matching:
            DeadlineActivityFactory.create_batch(
                3,
                status='open',
                initiative=initiative,
                office_location=matching_office
            )

        other_office = LocationFactory.create()
        other = InitiativeFactory.create_batch(2, status='approved')
        for initiative in other:
            DeadlineActivityFactory.create_batch(
                3,
                status='open',
                initiative=initiative,
                office_location=other_office
            )

        self.search({'office': matching_office.pk})
        self.assertFacets(
            'office',
            {
                str(matching_office.pk): len(matching),
                str(other_office.pk): len(other)
            },
            active=str(matching_office.pk)
        )
        self.assertFound(matching)

    def test_filter_theme(self):
        matching_theme, other_theme = ThemeFactory.create_batch(2)

        matching = InitiativeFactory.create_batch(2, status='approved', theme=matching_theme)
        other = InitiativeFactory.create_batch(3, status='approved', theme=other_theme)

        self.search({'theme': matching_theme.pk})
        self.assertFacets(
            'theme',
            {
                str(matching_theme.pk): len(matching),
                str(other_theme.pk): len(other)
            }
        )
        self.assertFound(matching)

    def test_filter_category(self):
        matching_category, other_category = CategoryFactory.create_batch(2)

        matching = InitiativeFactory.create_batch(2, status='approved')
        for initiative in matching:
            initiative.categories.add(matching_category)

        other = InitiativeFactory.create_batch(3, status='approved')
        for initiative in other:
            initiative.categories.add(other_category)

        self.search({'category': matching_category.pk})
        self.assertFacets(
            'category',
            {
                str(matching_category.pk): len(matching),
                str(other_category.pk): len(other)
            }
        )
        self.assertFound(matching)

    def test_search(self):
        text = 'lorem ipsum'
        matching = [
            InitiativeFactory.create(title='Lorem ipsum dolor sit amet', status='approved'),
            InitiativeFactory.create(title='Other title', pitch="Lorem ipsum", status='approved')
        ]
        InitiativeFactory.create(title='consectetur adipiscing elit', status='approved')
        InitiativeFactory.create(title='Nam eu turpis erat', status='approved')

        self.search({'search': text})
        self.assertFound(matching)

    def test_sort_created(self):
        matching = InitiativeFactory.create_batch(3, status='approved')

        matching[0].created = datetime.datetime(2018, 5, 7, tzinfo=get_current_timezone())
        matching[0].save()

        matching[1].created = datetime.datetime(2018, 5, 8, tzinfo=get_current_timezone())
        matching[1].save()

        matching[2].created = datetime.datetime(2018, 5, 9, tzinfo=get_current_timezone())
        matching[2].save()

        self.search({}, 'date_created')
        self.assertFound(matching)

    def test_sort_open_activities(self):
        matching = InitiativeFactory.create_batch(3, status='approved')

        matching[0].created = datetime.datetime(2018, 5, 7, tzinfo=get_current_timezone())
        DeedFactory.create_batch(4, initiative=matching[0], status='open')
        matching[0].save()

        matching[1].created = datetime.datetime(2018, 5, 8, tzinfo=get_current_timezone())
        DeedFactory.create_batch(2, initiative=matching[0], status='open')
        DeedFactory.create_batch(5, initiative=matching[0], status='succeeded')
        matching[1].save()

        matching[2].created = datetime.datetime(2018, 5, 9, tzinfo=get_current_timezone())
        DeedFactory.create_batch(2, initiative=matching[0], status='open')
        DeedFactory.create_batch(3, initiative=matching[0], status='succeeded')
        matching[2].save()

        self.search({}, 'open_activities')
        self.assertFound(matching)


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

    def test_detail_translation(self):
        theme = ThemeFactory.create(slug='world', name='Zooi')
        theme.set_current_language('en')
        theme.name = 'World domination'
        theme.save()
        url = reverse('initiative-theme', args=(theme.id,))
        response = self.client.get(
            url,
            user=self.user,
            HTTP_X_APPLICATION_LANGUAGE='en'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()['data']
        self.assertEqual(result['attributes']['name'], 'World domination')

    def test_detail_translation_missing(self):
        theme = Theme.objects.create(slug='world')
        theme.set_current_language('en')
        theme.name = 'World domination'
        theme.save()
        url = reverse('initiative-theme', args=(theme.id,))
        response = self.client.get(
            url,
            user=self.user,
            HTTP_X_APPLICATION_LANGUAGE='nl'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()['data']
        self.assertEqual(result['attributes']['name'], 'World domination')

    def test_detail_translation_nl(self):
        theme = ThemeFactory.create(slug='world')
        theme.set_current_language('en')
        theme.name = 'World domination'
        theme.set_current_language('nl')
        theme.name = 'Wereldoverheersing'
        theme.save()
        url = reverse('initiative-theme', args=(theme.id,))
        response = self.client.get(
            url,
            user=self.user,
            HTTP_X_APPLICATION_LANGUAGE='nl'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()['data']
        self.assertEqual(result['attributes']['name'], 'Wereldoverheersing')


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


class InitiativePlatformSettingsApiTestCase(APITestCase):

    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettings.load()
        self.url = reverse('settings')

    def test_get_search_filter_settings(self):
        self.settings.include_full_activities = False
        self.settings.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['platform']['initiatives']['include_full_activities'])

        self.settings.include_full_activities = True
        self.settings.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['platform']['initiatives']['include_full_activities'])

    def test_get_office_restriction_settings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['platform']['initiatives']['enable_office_restrictions'])
        self.assertFalse(data['platform']['initiatives']['enable_office_regions'])
        self.assertEqual(data['platform']['initiatives']['default_office_restriction'], 'all')

        self.settings.enable_office_restrictions = True
        self.settings.enable_office_regions = True
        self.settings.default_office_restriction = 'office_subregion'
        self.settings.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['platform']['initiatives']['enable_office_restrictions'])
        self.assertTrue(data['platform']['initiatives']['enable_office_regions'])
        self.assertEqual(data['platform']['initiatives']['default_office_restriction'], 'office_subregion')

    def test_get_search_filters(self):
        self.settings.search_filters_activities.all().delete()
        self.settings.search_filters_initiatives.all().delete()

        for filter_type in ['date', 'distance', 'is_online']:
            self.settings.search_filters_activities.add(
                ActivitySearchFilter.objects.create(
                    settings=self.settings,
                    type=filter_type
                )
            )
        for filter_type in ['theme', 'country']:
            self.settings.search_filters_initiatives.add(
                InitiativeSearchFilter.objects.create(
                    settings=self.settings,
                    type=filter_type
                )
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data['platform']['initiatives']['search_filters_activities'],
            [
                {'type': 'date', 'name': 'Date', 'highlight': False, 'placeholder': 'Select a date'},
                {'type': 'distance', 'name': 'Distance', 'highlight': False, 'placeholder': 'Select a distance'},
                {'type': 'is_online', 'name': 'Online / In-person', 'highlight': False, 'placeholder': 'Make a choice'}
            ]

        )
        self.assertEqual(
            data['platform']['initiatives']['search_filters_initiatives'],
            [
                {'type': 'theme', 'name': 'Theme', 'highlight': False, 'placeholder': 'Select a theme'},
                {'type': 'country', 'name': 'Country', 'highlight': False, 'placeholder': 'Select a country'}
            ]

        )

        self.settings.search_filters_initiatives.add(
            InitiativeSearchFilter.objects.create(
                settings=self.settings,
                type='old_filter'
            )
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data['platform']['initiatives']['search_filters_initiatives'],
            [
                {'type': 'theme', 'name': 'Theme', 'highlight': False, 'placeholder': 'Select a theme'},
                {'type': 'country', 'name': 'Country', 'highlight': False, 'placeholder': 'Select a country'},
                {'type': 'old_filter', 'name': '--------', 'highlight': False, 'placeholder': 'Select a --------'}
            ]
        )
