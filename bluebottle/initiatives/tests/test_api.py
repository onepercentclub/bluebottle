import datetime
import json

from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test import tag
from django.test.utils import override_settings
from django.utils.timezone import get_current_timezone
from django_elasticsearch_dsl.test import ESTestCase
from rest_framework import status

from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory, LocationFactory
from bluebottle.test.factory_models.projects import ProjectThemeFactory
from bluebottle.test.utils import JSONAPITestClient


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
            unicode(self.owner.pk)
        )
        self.assertEqual(
            response_data['data']['relationships']['theme']['data']['id'],
            unicode(initiative.theme.pk)
        )
        self.assertEqual(len(response_data['included']), 2)

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
        self.url = reverse('initiative-detail', args=(self.initiative.pk,))

    def test_patch(self):
        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                }
            }
        }
        response = self.client.patch(
            self.url,
            json.dumps(data),
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
            unicode(location.pk)
        )

        self.assertEqual(
            get_include(response, 'locations')['attributes']['name'],
            location.name
        )

    def test_patch_anonymous(self):
        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                }
            }
        }

        response = self.client.patch(
            self.url,
            json.dumps(data),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_wrong_user(self):
        data = {
            'data': {
                'id': self.initiative.id,
                'type': 'initiatives',
                'attributes': {
                    'title': 'Some title'
                }
            }
        }

        response = self.client.patch(
            self.url,
            json.dumps(data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_owner(self):
        response = self.client.get(
            self.url,
            user=self.owner
        )

        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.initiative.title)
        self.assertEqual(data['meta']['status'], self.initiative.status)
        self.assertEqual(data['meta']['transitions'], [{'name': 'submit', 'target': 'submitted'}])
        self.assertEqual(data['relationships']['theme']['data']['id'], unicode(self.initiative.theme.pk))
        self.assertEqual(data['relationships']['owner']['data']['id'], unicode(self.initiative.owner.pk))

        geolocation = get_include(response, 'geolocations')
        self.assertEqual(geolocation['attributes']['position'], {'latitude': 43.0579025, 'longitude': 23.6851594})

    def test_get_other(self):
        response = self.client.get(
            self.url,
            user=BlueBottleUserFactory.create()
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
        InitiativeFactory.create(owner=self.owner)
        InitiativeFactory.create()

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )
        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)

    def test_filter_owner(self):
        InitiativeFactory.create(owner=self.owner)
        InitiativeFactory.create()

        response = self.client.get(
            self.url + '?filter[owner.id]={}'.format(self.owner.pk),
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 1)
        self.assertEqual(data['data'][0]['relationships']['owner']['data']['id'], unicode(self.owner.pk))

    def test_search(self):
        first = InitiativeFactory.create(title='Lorem ipsum dolor sit amet', pitch="Lorem ipsum")
        InitiativeFactory.create(title='consectetur adipiscing elit')
        InitiativeFactory.create(title='Nam eu turpis erat')
        second = InitiativeFactory.create(title='Lorem ipsum dolor sit amet')

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(first.pk))
        self.assertEqual(data['data'][1]['id'], unicode(second.pk))

    def test_search_boost(self):
        first = InitiativeFactory.create(title='Something else', pitch='Lorem ipsum dolor sit amet')
        second = InitiativeFactory.create(title='Lorem ipsum dolor sit amet', pitch="Something else")

        response = self.client.get(
            self.url + '?filter[search]=lorem ipsum',
            HTTP_AUTHORIZATION="JWT {0}".format(self.owner.get_jwt_token())
        )

        data = json.loads(response.content)

        self.assertEqual(data['meta']['pagination']['count'], 2)
        self.assertEqual(data['data'][0]['id'], unicode(second.pk))
        self.assertEqual(data['data'][1]['id'], unicode(first.pk))

    def test_sort_title(self):
        second = InitiativeFactory.create(title='B: something else')
        first = InitiativeFactory.create(title='A: something')
        third = InitiativeFactory.create(title='C: More')

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
        first = InitiativeFactory.create()
        second = InitiativeFactory.create()
        third = InitiativeFactory.create()

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


class InitiativeReviewTransitionListAPITestCase(InitiativeAPITestCase):
    def setUp(self):
        super(InitiativeReviewTransitionListAPITestCase, self).setUp()

        self.url = reverse('initiative-review-transition-list')

        self.initiative = InitiativeFactory(
            owner=self.owner
        )

    def test_transition_to_submitted(self):
        data = {
            'data': {
                'type': 'initiative-transitions',
                'attributes': {
                    'transition': 'submit',
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        initiative = Initiative.objects.get(pk=self.initiative.pk)
        self.assertEqual(initiative.status, 'submitted')
        self.assertTrue(data['data']['id'])
        self.assertEqual(data['data']['attributes']['transition'], 'submit')

    def test_transition_disallowed(self):
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
        self.assertEqual(initiative.status, 'created')
