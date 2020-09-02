import datetime
import json

from django.contrib.auth.models import Group, Permission
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse
from django.test import TestCase, tag
from django.test.utils import override_settings
from django.utils.timezone import get_current_timezone, now

from moneyed import Money
from django_elasticsearch_dsl.test import ESTestCase
from rest_framework import status

from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory, LocationFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.projects import ProjectThemeFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import JSONAPITestClient, BluebottleTestCase


def get_include(response, name):
    included = response.json()['included']
    return [include for include in included if include['type'] == name][0]


class InitiativeAPITestCase(TestCase):
    """
    Integration tests for the Categories API.
    """

    def setUp(self):
        super(InitiativeAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        self.visitor = BlueBottleUserFactory.create()


class InitiativeListAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeListAPITestCase, self).setUp()
        self.theme = ProjectThemeFactory.create()
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

    def test_create_validation_organization_website(self):
        organization = OrganizationFactory.create(website='')

        data = {
            'data': {
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title',
                    'has_organization': True
                },
                'relationships': {
                    'organization': {
                        'data': {
                            'type': 'organizations',
                            'id': organization.pk
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
        organization = get_include(response, 'organizations')
        self.assertTrue(
            '/data/attributes/website' in (error['source']['pointer'] for error in organization['meta']['required'])
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

    def test_put_image(self):
        file_path = './bluebottle/files/tests/files/test-image.png'
        with open(file_path) as test_file:
            response = self.client.post(
                reverse('image-list'),
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="some_file.jpg"',
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

    def test_put_location(self):
        location = LocationFactory.create()

        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'initiatives',
                'relationships': {
                    'location': {
                        'data': {
                            'type': 'locations',
                            'id': location.pk
                        }
                    }
                }
            }
        }
        response = self.client.patch(
            self.url,
            json.dumps(data),
            content_type="application/vnd.api+json",
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(
            data['data']['relationships']['location']['data']['id'],
            str(location.pk)
        )

        self.assertEqual(
            get_include(response, 'locations')['attributes']['name'],
            location.name
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
                'target': 'needs_work'
            }])
        self.assertEqual(data['relationships']['theme']['data']['id'], str(self.initiative.theme.pk))
        self.assertEqual(data['relationships']['owner']['data']['id'], str(self.initiative.owner.pk))

        geolocation = get_include(response, 'geolocations')
        self.assertEqual(geolocation['attributes']['position'], {'latitude': 43.0579025, 'longitude': 23.6851594})

        self.assertTrue(
            '/data/attributes/title' in (error['source']['pointer'] for error in data['meta']['required'])
        )

    def test_get_activities(self):
        event = EventFactory.create(initiative=self.initiative)
        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 1)
        self.assertEqual(data['relationships']['activities']['data'][0]['id'], str(event.pk))
        self.assertEqual(data['relationships']['activities']['data'][0]['type'], 'activities/events')
        activity_data = get_include(response, 'activities/events')
        self.assertEqual(
            activity_data['attributes']['title'],
            event.title
        )
        self.assertEqual(activity_data['type'], 'activities/events')
        activity_location = activity_data['relationships']['location']['data']

        self.assertTrue(
            activity_location in (
                {'type': included['type'], 'id': included['id']} for included in response.json()['included']
            )
        )

    def test_deleted_activities(self):
        EventFactory.create(initiative=self.initiative, status='deleted')
        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data['relationships']['activities']['data']), 0)

    def test_get_stats(self):
        event = EventFactory.create(initiative=self.initiative, status='succeeded')
        ParticipantFactory.create_batch(3, activity=event, status='succeeded', time_spent=3)

        assignment = AssignmentFactory.create(initiative=self.initiative, status='succeeded', duration=3)
        ApplicantFactory.create_batch(3, activity=assignment, status='succeeded', time_spent=3)

        funding = FundingFactory.create(initiative=self.initiative, status='succeeded')
        DonationFactory.create_batch(3, activity=funding, status='succeeded', amount=Money(10, 'EUR'))
        DonationFactory.create_batch(3, activity=funding, status='succeeded', amount=Money(10, 'USD'))

        response = self.client.get(
            self.url,
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.json()['data']['meta']['stats']
        self.assertEqual(stats['hours'], 18)
        self.assertEqual(stats['activities'], 3)
        self.assertEqual(stats['contributions'], 12)
        self.assertEqual(stats['amount'], 75.0)

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

    def test_many_results(self):
        InitiativeFactory.create_batch(39, owner=self.owner, status='approved')
        InitiativeFactory.create(status="approved")

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 40)
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

    def test_filter_owner(self):
        InitiativeFactory.create_batch(2, status='submitted', owner=self.owner)
        InitiativeFactory.create_batch(4, status='submitted')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['relationships']['owner']['data']['id'], str(self.owner.pk))

    def test_filter_owner_activity(self):
        InitiativeFactory.create_batch(4, status='submitted')

        with_activity = InitiativeFactory.create(status='submitted')
        activity = EventFactory.create(owner=self.owner, initiative=with_activity)

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['relationships']['activities']['data'][0]['id'], str(activity.pk))

    def test_filter_location(self):
        location = LocationFactory.create()
        initiative = InitiativeFactory.create(status='approved', location=location)
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
        InitiativeFactory.create_batch(2, status='submitted', activity_manager=self.owner)
        InitiativeFactory.create_batch(4, status='approved')

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['relationships']['activity-manager']['data']['id'], str(self.owner.pk))

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
        InitiativeFactory.create_batch(2, status='submitted', activity_manager=self.owner)
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
        first = InitiativeFactory.create(status='approved', location=location)

        second = InitiativeFactory.create(status='approved', title='nameofoffice')

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
        EventFactory.create(
            initiative=second,
            status='open',
            start=now() + datetime.timedelta(days=7)
        )
        third = InitiativeFactory.create(status='approved')
        EventFactory.create(
            initiative=third,
            status='open',
            start=now() + datetime.timedelta(days=7)
        )
        AssignmentFactory.create(
            initiative=third,
            status='open',
            date=now() + datetime.timedelta(days=9)
        )

        response = self.client.get(
            self.url + '?sort=activity_date',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 3)
        self.assertEqual(data['data'][0]['id'], str(third.pk))
        self.assertEqual(data['data'][1]['id'], str(first.pk))
        self.assertEqual(data['data'][2]['id'], str(second.pk))


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
        self.assertEqual(data['errors'][0], 'Transition is not available')

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

    def test_event(self):
        event = EventFactory.create()
        task = TaskFactory.create(type='event', activity_id=event.pk)

        data = {
            'data': {
                'type': 'initiative-redirects',
                'attributes': {
                    'route': 'task',
                    'params': {'task_id': task.pk}
                },
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            response.json()['data']['attributes']['target-route'], 'initiatives.activities.details.event'
        )

        self.assertEqual(
            response.json()['data']['attributes']['target-params'], [event.pk, event.slug]
        )

    def test_assignment(self):
        assignment = AssignmentFactory.create()
        task = TaskFactory.create(activity_id=assignment.pk)

        data = {
            'data': {
                'type': 'initiative-redirects',
                'attributes': {
                    'route': 'task',
                    'params': {'task_id': task.pk}
                },
            }
        }
        response = self.client.post(
            self.url,
            json.dumps(data)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            response.json()['data']['attributes']['target-route'], 'initiatives.activities.details.assignment'
        )

        self.assertEqual(
            response.json()['data']['attributes']['target-params'], [assignment.pk, assignment.slug]
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

        with open(file_path) as test_file:
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
            '/api/initiatives/{}/related-image/600'.format(response.json()['data']['id'])
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


class ThemeListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(ThemeListAPITestCase, self).setUp()

        self.client = JSONAPITestClient()
        for theme in ProjectTheme.objects.all():
            theme.delete()

        self.url = reverse('initiative-theme-list')
        self.user = BlueBottleUserFactory()

        ProjectThemeFactory.create_batch(5, disabled=False)

    def test_list(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )
        result = response.json()['data'][0]

        theme = ProjectTheme.objects.get(pk=result['id'])

        self.assertEqual(theme.name, result['attributes']['name'])

    def test_list_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )

    def test_list_closed(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_disabled(self):
        ProjectThemeFactory.create(disabled=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )
