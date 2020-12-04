import json
from datetime import timedelta, date, datetime

from urllib.parse import urlparse, parse_qs

from django.contrib.auth.models import Group, Permission
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils.timezone import now, utc, get_current_timezone

import icalendar

from rest_framework import status

from bluebottle.time_based.tests.factories import (
    DateActivityFactory, PeriodActivityFactory,
    DateParticipantFactory, PeriodParticipantFactory
)
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class TimeBasedListAPIViewTestCase():
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.client = JSONAPITestClient()
        self.url = reverse('{}-list'.format(self.type))
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)
        self.initiative.states.submit(save=True)

        self.data = {
            'data': {
                'type': 'activities/time-based/{}s'.format(self.type),
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'review': False,
                    'is-online': True,
                    'registration-deadline': str(date.today() + timedelta(days=14)),
                    'capacity': 10,
                    'description': 'We will clean up the beach south of Katwijk'
                },
                'relationships': {
                    'initiative': {
                        'data': {
                            'type': 'initiatives', 'id': self.initiative.id
                        },
                    },
                }
            }
        }

    def test_create_complete(self):
        response = self.client.post(self.url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()['data']

        self.assertEqual(data['attributes']['status'], 'draft')
        self.assertEqual(data['attributes']['title'], self.data['data']['attributes']['title'])
        self.assertEqual(
            {
                transition['name'] for transition in
                data['meta']['transitions']
            },
            {'submit', 'delete'}
        )
        self.assertEqual(
            data['meta']['permissions']['GET'],
            True
        )

        self.assertEqual(
            data['meta']['permissions']['PUT'],
            True
        )

        self.assertEqual(
            data['meta']['permissions']['PATCH'],
            True
        )

    def test_create_duplicate_title(self):
        DateActivityFactory.create(
            title=self.data['data']['attributes']['title']
        )

        # Add an activity with the same title should NOT return an error
        response = self.client.post(self.url, json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_disabled(self):
        self.settings.activity_types = ('funding', )
        self.settings.save()

        response = self.client.post(self.url, json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_no_title(self):
        del self.data['data']['attributes']['title']
        response = self.client.post(self.url, json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            '/data/attributes/title' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )

    def test_create_no_location(self):
        self.data['data']['attributes']['is-online'] = False

        response = self.client.post(self.url, json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            '/data/attributes/location' not in (
                error['source']['pointer'] for error in response.json()['data']['meta']['errors']
            )
        )

        response = self.client.post(self.url, json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            '/data/attributes/location' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )

    def test_create_as_activity_manager(self):
        activity_manager = BlueBottleUserFactory.create()
        self.initiative.activity_manager = activity_manager
        self.initiative.save()

        response = self.client.post(self.url, json.dumps(self.data), user=activity_manager)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_not_initiator(self):
        another_user = BlueBottleUserFactory.create()
        response = self.client.post(self.url, json.dumps(self.data), user=another_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DateListAPIViewTestCase(TimeBasedListAPIViewTestCase, BluebottleTestCase):
    type = 'date'
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def setUp(self):
        super().setUp()

        self.data['data']['attributes'].update({
            'start': str(now() + timedelta(days=21)),
            'duration': '4:00:00',
        })


class PeriodListAPIViewTestCase(TimeBasedListAPIViewTestCase, BluebottleTestCase):
    type = 'period'
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def setUp(self):
        super().setUp()

        self.data['data']['attributes'].update({
            'deadline': str(date.today() + timedelta(days=21)),
            'duration': '4:00:00',
            'duration_period': 'overall',
        })


class TimeBasedDetailAPIViewTestCase():
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.factory._meta.model.__name__.lower()]
        )

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.activity = self.factory.create()

        self.url = reverse('{}-detail'.format(self.type), args=(self.activity.pk, ))

        self.data = {
            'data': {
                'type': 'activities/time-based/{}s'.format(self.type),
                'id': str(self.activity.pk),
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'review': False,
                    'is-online': True,
                    'registration-deadline': str(date.today() + timedelta(days=14)),
                    'capacity': 10,
                    'description': 'We will clean up the beach south of Katwijk'
                },
                'relationships': {
                    'initiative': {
                        'data': {
                            'type': 'initiatives', 'id': self.activity.initiative.id
                        },
                    },
                }
            }
        }

    def test_get_owner(self):
        response = self.client.get(self.url, user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['attributes']['title'], self.activity.title)

        self.assertEqual(
            data['meta']['permissions']['GET'],
            True
        )

        self.assertEqual(
            data['meta']['permissions']['PUT'],
            True
        )

        self.assertEqual(
            data['meta']['permissions']['PATCH'],
            True
        )
        self.assertTrue(
            {'name': 'delete', 'target': 'deleted', 'available': True}
            in data['meta']['transitions']
        )

    def test_get_open(self):
        self.activity.initiative.states.submit(save=True)
        self.activity.initiative.states.approve(save=True)

        response = self.client.get(self.url, user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.data = response.json()['data']

        self.assertTrue(
            {'name': 'cancel', 'target': 'cancelled', 'available': True}
            in self.data['meta']['transitions']
        )

    def test_get_contributors(self):
        self.participant_factory.create_batch(4, activity=self.activity)
        self.participant_factory.create(activity=self.activity, user=self.activity.owner)
        response = self.client.get(self.url, user=self.activity.owner)

        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        contributor_ids = [
            resource['id'] for resource in data['relationships']['contributors']['data']
        ]

        self.assertEqual(
            len(data['relationships']['contributors']['data']),
            5
        )
        contributor_response = self.client.get(
            data['relationships']['contributors']['links']['related'],
            user=self.activity.owner
        )
        contributor_data = contributor_response.json()
        self.assertEqual(contributor_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            contributor_data['meta']['pagination']['count'], len(contributor_ids)
        )
        for contributor in contributor_data['data']:
            self.assertTrue(
                contributor['id'] in contributor_ids
            )

    def test_get_non_anonymous(self):
        response = self.client.get(self.url)

        data = response.json()['data']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['attributes']['title'], self.activity.title)

        self.assertEqual(
            data['meta']['permissions']['GET'],
            True
        )

        self.assertEqual(
            data['meta']['permissions']['PUT'],
            False
        )

        self.assertEqual(
            data['meta']['permissions']['PATCH'],
            False
        )

    def test_update_owner(self):
        response = self.client.put(self.url, json.dumps(self.data), user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()['data']['attributes']['title'],
            self.data['data']['attributes']['title']
        )

    def test_update_unauthenticated(self):
        response = self.client.put(self.url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_wrong_user(self):
        response = self.client.put(
            self.url, json.dumps(self.data), user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_owner(self):
        response = self.client.delete(self.url, user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_unauthenticated(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_wrong_user(self):
        response = self.client.delete(
            self.url, user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_submitted(self):
        self.activity.initiative.states.submit(save=True)
        response = self.client.delete(
            self.url, user=self.activity.owner
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_cancelled(self):
        self.activity.initiative.states.submit(save=True)
        self.activity.initiative.states.approve(save=True)

        self.activity.refresh_from_db()
        self.activity.states.cancel(save=True)

        response = self.client.put(self.url, json.dumps(self.data), user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_deleted(self):
        self.activity.states.delete(save=True)
        response = self.client.put(self.url, json.dumps(self.data), user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_rejected(self):
        self.activity.states.reject(save=True)
        response = self.client.put(self.url, json.dumps(self.data), user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DateDetailAPIViewTestCase(TimeBasedDetailAPIViewTestCase, BluebottleTestCase):
    type = 'date'
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    def setUp(self):
        super().setUp()

        self.data['data']['attributes'].update({
            'start': str(now() + timedelta(days=21)),
            'duration': '4:00',
        })

    def test_get_utc_offset(self):
        self.activity.location.position = Point(4.8888, 52.399)
        self.activity.location.save()

        self.activity.start = get_current_timezone().localize(
            datetime(2025, 2, 23, 10, 00)
        )
        self.activity.save()

        response = self.client.get(self.url)
        self.assertEqual(
            response.json()['data']['attributes']['utc-offset'], 60.0
        )

    def test_get_utc_offset_summertime(self):
        self.activity.location.position = Point(4.8888, 52.399)
        self.activity.location.save()

        self.activity.start = get_current_timezone().localize(
            datetime(2025, 7, 23, 10, 00)
        )
        self.activity.save()

        response = self.client.get(self.url)
        self.assertEqual(
            response.json()['data']['attributes']['utc-offset'], 120.0
        )

    def test_get_utc_offset_new_york(self):
        self.activity.location.position = Point(-74.259, 40.697)
        self.activity.location.save()

        self.activity.start = get_current_timezone().localize(
            datetime(2025, 7, 23, 10, 00)
        )
        self.activity.save()

        response = self.client.get(self.url)
        self.assertEqual(
            response.json()['data']['attributes']['utc-offset'], -240.0
        )

    def test_get_calendar_links(self):
        response = self.client.get(self.url, user=self.activity.owner)

        links = response.json()['data']['attributes']['links']
        google_link = urlparse(links['google'])
        google_query = parse_qs(google_link.query)

        self.assertEqual(google_link.netloc, 'calendar.google.com')
        self.assertEqual(google_link.path, '/calendar/render')

        self.assertEqual(google_query['action'][0], 'TEMPLATE')
        self.assertEqual(google_query['location'][0], self.activity.location.formatted_address)
        self.assertEqual(google_query['text'][0], self.activity.title)
        self.assertEqual(google_query['uid'][0], 'test-dateactivity-{}'.format(self.activity.pk))

        details = (
            u"{}\n"
            u"http://testserver/en/initiatives/activities/details/"
            u"dateactivity/{}/{}"
        ).format(
            self.activity.description, self.activity.pk, self.activity.slug
        )

        self.assertEqual(google_query['details'][0], details)
        self.assertEqual(
            google_query['dates'][0],
            u'{}/{}'.format(
                self.activity.start.astimezone(utc).strftime('%Y%m%dT%H%M%SZ'),
                (self.activity.start + self.activity.duration).astimezone(utc).strftime('%Y%m%dT%H%M%SZ')
            )
        )

        outlook_link = urlparse(links['outlook'])
        outlook_query = parse_qs(outlook_link.query)

        self.assertEqual(outlook_link.netloc, 'outlook.live.com')
        self.assertEqual(outlook_link.path, '/owa/')

        self.assertEqual(outlook_query['rru'][0], 'addevent')
        self.assertEqual(outlook_query['path'][0], u'/calendar/action/compose&rru=addevent')
        self.assertEqual(outlook_query['location'][0], self.activity.location.formatted_address)
        self.assertEqual(outlook_query['subject'][0], self.activity.title)
        self.assertEqual(outlook_query['body'][0], details)
        self.assertEqual(
            outlook_query['startdt'][0],
            self.activity.start.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S')
        )
        self.assertEqual(
            outlook_query['enddt'][0],
            (self.activity.start + self.activity.duration).astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S')
        )

        self.assertTrue(
            links['ical'].startswith(reverse('date-ical', args=(self.activity.pk, )))
        )


class PeriodDetailAPIViewTestCase(TimeBasedDetailAPIViewTestCase, BluebottleTestCase):
    type = 'period'
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    def setUp(self):
        super().setUp()

        self.data['data']['attributes'].update({
            'deadline': str(date.today() + timedelta(days=21)),
        })

    def test_get_open(self):
        super().test_get_open()

        self.assertFalse(
            {'name': 'succeed_manually', 'target': 'succeeded', 'available': True}
            in self.data['meta']['transitions']
        )

    def test_get_open_with_participant(self):
        self.activity.duration_period = 'weeks'
        self.activity.save()

        PeriodParticipantFactory.create(activity=self.activity)

        super().test_get_open()

        self.assertTrue(
            {'name': 'succeed_manually', 'target': 'succeeded', 'available': True}
            in self.data['meta']['transitions']
        )


class TimeBasedTransitionAPIViewTestCase():
    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.activity = self.factory.create()

        self.url = reverse('{}-transition-list'.format(self.type))
        self.data = {
            'data': {
                'type': 'activities/time-based/{}-transitions'.format(self.type),
                'attributes': {},
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'activities/time-based/{}s'.format(self.type),
                            'id': self.activity.pk
                        }
                    }
                }
            }
        }

    def test_delete_by_owner(self):
        # Owner can delete the event
        self.data['data']['attributes']['transition'] = 'delete'

        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=self.activity.owner
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(
            data['included'][0]['type'],
            'activities/time-based/{}s'.format(self.type)
        )
        self.assertEqual(data['included'][0]['attributes']['status'], 'deleted')

    def test_delete_by_other_user(self):
        self.data['data']['attributes']['transition'] = 'delete'

        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")

    def test_reject(self):
        self.data['data']['attributes']['transition'] = 'reject'
        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=self.activity.owner
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")

    def test_approve(self):
        self.data['data']['attributes']['transition'] = 'approve'
        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=self.activity.owner
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")


class OnADatteTransitionAPIViewTestCase(TimeBasedTransitionAPIViewTestCase, BluebottleTestCase):
    type = 'date'
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory


class PeriodTransitionAPIViewTestCase(TimeBasedTransitionAPIViewTestCase, BluebottleTestCase):
    type = 'period'
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory


class ParticipantListViewTestCase():
    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.activity = self.factory.create()

        self.url = reverse(self.url_name)

        self.private_document_url = reverse('private-document-list')
        self.png_document_path = './bluebottle/files/tests/files/test-image.png'

        self.data = {
            'data': {
                'type': self.participant_type,
                'attributes': {
                    'motiviation': 'I am great',
                },
                'relationships': {
                    'activity': {
                        'data': {
                            'type': 'activities/time-based/{}s'.format(self.type),
                            'id': self.activity.pk
                        }
                    }
                }
            }
        }

    def test_create(self):
        response = self.client.post(self.url, json.dumps(self.data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()['data']
        self.assertEqual(
            data['relationships']['user']['data']['id'],
            str(self.user.pk)
        )

        self.assertEqual(
            data['meta']['permissions']['GET'],
            True
        )

        self.assertEqual(
            data['meta']['permissions']['PUT'],
            True
        )

        self.assertEqual(
            data['meta']['permissions']['PATCH'],
            True
        )

    def test_create_with_document(self):
        with open(self.png_document_path, 'rb') as test_file:
            document_response = self.client.post(
                self.private_document_url,
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="test.rtf"',
                user=self.user
            )

            self.assertEqual(document_response.status_code, 201)
            document_data = json.loads(document_response.content)

        self.data['data']['relationships']['document'] = {
            'data': {
                'type': 'private-documents',
                'id': document_data['data']['id']
            }
        }

        response = self.client.post(self.url, json.dumps(self.data), user=self.user)

        data = response.json()['data']
        self.assertEqual(
            data['relationships']['document']['data']['id'],
            document_data['data']['id']
        )

    def test_create_duplicate(self):
        self.client.post(self.url, json.dumps(self.data), user=self.user)
        response = self.client.post(self.url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['errors'][0]['detail'],
            'The fields activity, user must make a unique set.'
        )

    def test_create_anonymous(self):
        response = self.client.post(self.url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DateParticipantListAPIViewTestCase(ParticipantListViewTestCase, BluebottleTestCase):
    type = 'date'
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory

    url_name = 'on-a-date-participant-list'
    application_type = 'contributions/time-based/date-participants'
    url_name = 'date-participant-list'
    participant_type = 'contributors/time-based/date-participants'


class PeriodParticipantListAPIViewTestCase(ParticipantListViewTestCase, BluebottleTestCase):
    type = 'period'
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory

    url_name = 'period-participant-list'
    participant_type = 'contributors/time-based/period-participants'


class ParticipantDetailViewTestCase():
    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.activity = self.factory.create()
        self.participant = self.participant_factory(
            activity=self.activity,
            motivation='My motivation'
        )

        self.url = reverse(self.url_name, args=(self.participant.pk, ))

        self.private_document_url = reverse('private-document-list')
        self.png_document_path = './bluebottle/files/tests/files/test-image.png'

        self.data = {
            'data': {
                'type': self.participant_type,
                'id': self.participant.pk,
                'attributes': {'motivation': 'Let\'s go!!!'},
            }
        }

    def test_get_user(self):
        response = self.client.get(self.url, user=self.participant.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']

        self.assertEqual(
            data['attributes']['motivation'],
            self.participant.motivation
        )

        self.assertEqual(
            data['relationships']['user']['data']['id'],
            str(self.participant.user.pk)
        )

        self.assertEqual(
            data['meta']['permissions']['GET'],
            True
        )

        self.assertEqual(
            data['meta']['permissions']['PUT'],
            True
        )

        self.assertEqual(
            data['meta']['permissions']['PATCH'],
            True
        )
        self.assertTrue(
            {'name': 'withdraw', 'target': 'withdrawn', 'available': True}
            in data['meta']['transitions']
        )

    def test_get_owner(self):
        response = self.client.get(self.url, user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.data = response.json()['data']

        self.assertEqual(
            self.data['attributes']['motivation'],
            self.participant.motivation
        )

        self.assertFalse(
            {'name': 'withdraw', 'target': 'withdrawn', 'available': True}
            in self.data['meta']['transitions']
        )

        self.assertTrue(
            {'name': 'reject', 'target': 'rejected', 'available': True}
            in self.data['meta']['transitions']
        )

    def test_get_activity_manager(self):
        response = self.client.get(self.url, user=self.activity.initiative.activity_manager)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']

        self.assertEqual(
            data['attributes']['motivation'],
            self.participant.motivation
        )

    def test_get_other_user(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']

        self.assertIsNone(
            data['attributes']['motivation']
        )

    def test_patch_user(self):
        response = self.client.patch(self.url, json.dumps(self.data), user=self.participant.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']

        self.assertEqual(
            data['attributes']['motivation'],
            self.data['data']['attributes']['motivation']
        )

    def test_patch_document(self):
        with open(self.png_document_path, 'rb') as test_file:
            document_response = self.client.post(
                self.private_document_url,
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="test.rtf"',
                user=self.user
            )

            self.assertEqual(document_response.status_code, 201)
            document_data = json.loads(document_response.content)

        self.data['data']['relationships'] = {
            'document': {
                'data': {
                    'type': 'private-documents',
                    'id': document_data['data']['id']
                }
            }
        }

        response = self.client.patch(self.url, json.dumps(self.data), user=self.participant.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']

        self.assertEqual(
            data['relationships']['document']['data']['id'],
            document_data['data']['id']
        )

    def test_patch_other_user(self):
        response = self.client.patch(self.url, json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_anonymous(self):
        response = self.client.patch(self.url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DateParticipantDetailAPIViewTestCase(ParticipantDetailViewTestCase, BluebottleTestCase):
    type = 'date'
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory
    url_name = 'date-participant-detail'
    participant_type = 'contributors/time-based/date-participants'


class PeriodParticipantDetailAPIViewTestCase(ParticipantDetailViewTestCase, BluebottleTestCase):
    type = 'period'
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory
    url_name = 'period-participant-detail'
    participant_type = 'contributors/time-based/period-participants'

    def test_get_owner(self):
        super().test_get_owner()
        self.assertTrue(
            {'name': 'reject', 'target': 'rejected', 'available': True}
            in self.data['meta']['transitions']
        )


class ParticipantTransitionAPIViewTestCase():
    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.activity = self.factory.create()
        self.participant = self.participant_factory.create(
            activity=self.activity
        )

        self.url = reverse(self.url_name)
        self.data = {
            'data': {
                'type': '{}-transitions'.format(self.participant_type),
                'attributes': {},
                'relationships': {
                    'resource': {
                        'data': {
                            'type': '{}s'.format(self.participant_type),
                            'id': self.participant.pk
                        }
                    }
                }
            }
        }

    def test_withdraw_by_user(self):
        # Owner can delete the event
        self.data['data']['attributes']['transition'] = 'withdraw'

        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=self.participant.user
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(
            data['included'][0]['type'],
            '{}s'.format(self.participant_type)
        )
        self.assertEqual(data['included'][0]['attributes']['status'], 'withdrawn')

    def test_withdraw_by_other_user(self):
        # Owner can delete the event
        self.data['data']['attributes']['transition'] = 'withdraw'

        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=self.user
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_by_activity_owner(self):
        # Owner can delete the event
        self.data['data']['attributes']['transition'] = 'reject'

        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=self.activity.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(
            data['included'][0]['type'],
            '{}s'.format(self.participant_type)
        )
        self.assertEqual(data['included'][0]['attributes']['status'], 'rejected')

    def test_reject_by_user(self):
        # Owner can delete the event
        self.data['data']['attributes']['transition'] = 'reject'

        response = self.client.post(
            self.url,
            json.dumps(self.data),
            user=self.participant.user
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OnADateParticipantTransitionAPIViewTestCase(ParticipantTransitionAPIViewTestCase, BluebottleTestCase):
    type = 'date'
    url_name = 'date-participant-transition-list'
    participant_type = 'contributors/time-based/date-participant'
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory


class PeriodParticipantTransitionAPIViewTestCase(ParticipantTransitionAPIViewTestCase, BluebottleTestCase):
    type = 'period'
    participant_type = 'contributors/time-based/period-participant'
    url_name = 'period-participant-transition-list'

    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory


class RelatedParticipantsAPIViewTestCase():
    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.activity = self.factory.create()
        self.participants = self.participant_factory.create_batch(
            5,
            activity=self.activity
        )
        self.participants[0].states.reject(save=True)

        self.url = reverse(self.url_name, args=(self.activity.pk,))

    def test_get_owner(self):
        response = self.client.get(self.url, user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json()['data']), 5)

        included_contributions = [
            resource for resource in response.json()['included']
            if resource['type'] == 'contributions/time-contributions'
        ]
        self.assertEqual(len(included_contributions), 5)

    def test_get_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json()['data']), 4)

    def test_get_closed_site(self):
        MemberPlatformSettings.objects.update(closed=True)
        group = Group.objects.get(name='Anonymous')
        group.permissions.remove(Permission.objects.get(codename='api_read_dateparticipant'))
        group.permissions.remove(Permission.objects.get(codename='api_read_periodparticipant'))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TimeContributionDetailAPIViewTestCase():
    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.activity = self.factory.create()
        self.participant = self.participant_factory.create(
            activity=self.activity
        )
        self.contribution = self.participant.contributions.get()

        self.url = reverse(
            'time-contribution-detail',
            args=(self.contribution.pk,)
        )
        self.data = {
            'data': {
                'type': 'contributions/time-contributions',
                'id': self.contribution.pk,
                'attributes': {
                    'value': '5:00:00'
                }
            }
        }

    def test_get_owner(self):
        response = self.client.get(self.url, user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_contributor(self):
        response = self.client.get(self.url, user=self.participant.user)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_other(self):
        response = self.client.get(self.url, user=BlueBottleUserFactory.create())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_owner(self):
        response = self.client.put(self.url, json.dumps(self.data), user=self.activity.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.contribution.refresh_from_db()

        self.assertEqual(self.contribution.value, timedelta(hours=5))

    def test_put_contributor(self):
        response = self.client.put(self.url, json.dumps(self.data), user=self.participant.user)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_other(self):
        response = self.client.put(self.url, json.dumps(self.data), user=BlueBottleUserFactory.create())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_anonymous(self):
        response = self.client.put(self.url, json.dumps(self.data))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OnADateTimeContributionAPIViewTestCase(TimeContributionDetailAPIViewTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory


class PeriodTimeContributionAPIViewTestCase(TimeContributionDetailAPIViewTestCase, BluebottleTestCase):
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory


class RelatedDateParticipantAPIViewTestCase(RelatedParticipantsAPIViewTestCase, BluebottleTestCase):
    type = 'date'
    url_name = 'date-participants'
    participant_type = 'contributors/time-based/date-participant'
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory


class RelatedPeriodParticipantAPIViewTestCase(RelatedParticipantsAPIViewTestCase, BluebottleTestCase):
    type = 'period'
    url_name = 'period-participants'
    participant_type = 'contributors/time-based/period-participant'
    factory = PeriodActivityFactory
    participant_factory = PeriodParticipantFactory


class DateIcalTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()

        self.activity = DateActivityFactory.create(title='Pollute Katwijk Beach')

        self.activity_url = reverse('date-detail', args=(self.activity.pk,))
        response = self.client.get(self.activity_url)

        self.signed_url = response.json()['data']['attributes']['links']['ical']
        self.unsigned_url = reverse('date-ical', args=(self.activity.pk,))

    def test_get(self):
        response = self.client.get(self.signed_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.get('content-type'), 'text/calendar')
        self.assertEqual(
            response.get('content-disposition'),
            'attachment; filename="{}.ics"'.format(self.activity.slug)
        )

        calendar = icalendar.Calendar.from_ical(response.content)

        for ical_event in calendar.walk('vevent'):
            self.assertAlmostEqual(
                ical_event['dtstart'].dt,
                self.activity.start,
                delta=timedelta(seconds=10)
            )
            self.assertAlmostEqual(
                ical_event['dtend'].dt,
                self.activity.start + self.activity.duration,
                delta=timedelta(seconds=10)
            )

            self.assertEqual(ical_event['dtstart'].dt.tzinfo, utc)
            self.assertEqual(ical_event['dtend'].dt.tzinfo, utc)

            self.assertEqual(str(ical_event['summary']), self.activity.title)
            self.assertEqual(
                str(ical_event['description']),
                '{}\n{}'.format(self.activity.description, self.activity.get_absolute_url())
            )
            self.assertEqual(ical_event['url'], self.activity.get_absolute_url())
            self.assertEqual(ical_event['organizer'], 'MAILTO:{}'.format(self.activity.owner.email))

    def test_get_no_signature(self):
        response = self.client.get(self.unsigned_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_wrong_signature(self):
        response = self.client.get('{}?signature=ewiorjewoijical_url'.format(self.unsigned_url))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
