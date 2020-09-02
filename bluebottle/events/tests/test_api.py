# coding=utf-8
import json
from datetime import timedelta
import urllib.parse

from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now, utc

import icalendar

from rest_framework import status

from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, get_included


class EventListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(EventListAPITestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['event']
        )

        self.client = JSONAPITestClient()
        self.url = reverse('event-list')
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)
        self.initiative.states.submit(save=True)

    def test_create_event_complete(self):
        start = now() + timedelta(days=21)
        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start': str(start),
                    'duration': 4,
                    'is_online': True,
                    'registration_deadline': str((now() + timedelta(days=14)).date()),
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
        response = self.client.post(self.url, json.dumps(data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'draft')
        self.assertEqual(response.data['title'], 'Beach clean-up Katwijk')
        self.assertEqual(
            [
                transition['name'] for transition in
                response.json()['data']['meta']['transitions']
            ],
            ['submit', 'delete']
        )

        # Add an event with the same title should NOT return an error
        response = self.client.post(self.url, json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_event_disabled(self):
        self.settings.activity_types = ('funding', )
        self.settings.save()

        start = now() + timedelta(days=21)
        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start': str(start),
                    'duration': 4,
                    'registration_deadline': str((now() + timedelta(days=14)).date()),
                    'capacity': 10,
                    'address': 'Zuid-Boulevard Katwijk aan Zee',
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
        response = self.client.post(self.url, json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_event_no_title(self):
        start = now() + timedelta(days=21)
        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'start': str(start),
                    'duration': 4,
                    'registration_deadline': str((now() + timedelta(days=14)).date()),
                    'capacity': 10,
                    'address': 'Zuid-Boulevard Katwijk aan Zee',
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
        response = self.client.post(self.url, json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            '/data/attributes/title' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )

    def test_create_event_no_location(self):
        start = now() + timedelta(days=21)
        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'start': str(start),
                    'is_online': False,
                    'duration': 4,
                    'registration_deadline': str((now() + timedelta(days=14)).date()),
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
        response = self.client.post(self.url, json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            '/data/attributes/location' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )

    def test_create_event_no_location_is_online(self):
        start = now() + timedelta(days=21)
        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'start': str(start),
                    'is_online': True,
                    'duration': 4,
                    'registration_deadline': str((now() + timedelta(days=14)).date()),
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
        response = self.client.post(self.url, json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            '/data/attributes/location' not in (
                error['source']['pointer'] for error in response.json()['data']['meta']['errors']
            )
        )

    def test_create_event_as_activity_manager(self):
        activity_manager = BlueBottleUserFactory.create()
        self.initiative.activity_manager = activity_manager
        self.initiative.save()

        start = now() + timedelta(days=21)
        registration = now() + timedelta(days=14)

        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start': str(start),
                    'registration_deadline': str(registration.date()),
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
        response = self.client.post(self.url, json.dumps(data), user=activity_manager)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'draft')
        self.assertEqual(response.data['title'], 'Beach clean-up Katwijk')

    def test_create_event_not_initiator(self):
        another_user = BlueBottleUserFactory.create()
        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start': str((now() + timedelta(days=21))),
                    'registration_deadline': str((now() + timedelta(days=14)).date()),
                    'capacity': 10,
                    'address': 'Zuid-Boulevard Katwijk aan Zee',
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
        response = self.client.post(self.url, json.dumps(data), user=another_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EventIcalTestCase(BluebottleTestCase):
    def test_get(self):
        event = EventFactory.create(title='Pollute Katwijk Beach')

        event_url = reverse('event-detail', args=(event.pk,))
        response = self.client.get(event_url)
        ical_url = response.json()['data']['attributes']['links']['ical']

        response = self.client.get(ical_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.get('content-type'), 'text/calendar')
        self.assertEqual(
            response.get('content-disposition'),
            'attachment; filename="{}.ics"'.format(event.slug)
        )

        calendar = icalendar.Calendar.from_ical(response.content)

        for ical_event in calendar.walk('vevent'):
            self.assertAlmostEqual(ical_event['dtstart'].dt, event.start, delta=timedelta(seconds=10))
            self.assertAlmostEqual(ical_event['dtend'].dt, event.end, delta=timedelta(seconds=10))

            self.assertEqual(ical_event['dtstart'].dt.tzinfo, utc)
            self.assertEqual(ical_event['dtend'].dt.tzinfo, utc)

            self.assertEqual(str(ical_event['summary']), event.title)
            self.assertEqual(
                str(ical_event['description']),
                '{}\n{}'.format(event.description, event.get_absolute_url())
            )
            self.assertEqual(str(ical_event['url']), event.get_absolute_url())
            self.assertEqual(str(ical_event['organizer']), 'MAILTO:{}'.format(event.owner.email))

    def test_get_no_signature(self):
        event = EventFactory.create(title='Pollute Katwijk Beach')

        ical_url = reverse('event-ical', args=(event.pk,))
        response = self.client.get(ical_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_wrong_signature(self):
        event = EventFactory.create(title='Pollute Katwijk Beach')

        ical_url = reverse('event-ical', args=(event.pk,))
        response = self.client.get('{}?signature=ewiorjewoijical_url'.format(ical_url))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EventDetailTestCase(BluebottleTestCase):
    def setUp(self):
        super(EventDetailTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.event = EventFactory.create(initiative=self.initiative, owner=self.owner)

        self.url = reverse('event-detail', args=(self.event.pk,))
        self.data = {
            'data': {
                'type': 'activities/events',
                'id': self.event.id,
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start': str(now() + timedelta(days=21)),
                    'duration': 4,
                    'registration_deadline': str((now() + timedelta(days=14)).date()),
                    'capacity': 10,
                    'address': 'Zuid-Boulevard Katwijk aan Zee',
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

    def test_get(self):
        response = self.client.get(self.url, user=self.event.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['attributes']['title'], self.event.title)

    def test_get_event_calendar_links(self):
        self.event.description = "Just kidding, <br/>we're going&nbsp;to clean it up of course 😉"
        self.event.save()
        response = self.client.get(self.url, user=self.event.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        links = response.data['links']
        google_link = urllib.parse.urlparse(links['google'])
        google_query = urllib.parse.parse_qs(google_link.query)

        self.assertEqual(google_link.netloc, 'calendar.google.com')
        self.assertEqual(google_link.path, '/calendar/render')

        self.assertEqual(google_query['action'][0], 'TEMPLATE')
        self.assertEqual(google_query['location'][0], self.event.location.formatted_address)
        self.assertEqual(google_query['text'][0], self.event.title)
        self.assertEqual(google_query['uid'][0], 'test-event-{}'.format(self.event.pk))
        details = "Just kidding, we're going\xc2\xa0to clean it up of course \xf0\x9f\x98\x89\n" \
                  "http://testserver/en/initiatives/activities/details/" \
                  "event/{}/{}".format(self.event.pk, self.event.slug)
        self.assertEqual(google_query['details'][0], details)
        self.assertEqual(
            google_query['dates'][0],
            '{}/{}'.format(
                self.event.start.astimezone(utc).strftime('%Y%m%dT%H%M%SZ'),
                self.event.end.astimezone(utc).strftime('%Y%m%dT%H%M%SZ')
            )
        )

        outlook_link = urllib.parse.urlparse(links['outlook'])
        outlook_query = urllib.parse.parse_qs(outlook_link.query)

        self.assertEqual(outlook_link.netloc, 'outlook.live.com')
        self.assertEqual(outlook_link.path, '/owa/')

        self.assertEqual(outlook_query['rru'][0], 'addevent')
        self.assertEqual(outlook_query['path'][0], '/calendar/action/compose&rru=addevent')
        self.assertEqual(outlook_query['location'][0], self.event.location.formatted_address)
        self.assertEqual(outlook_query['subject'][0], self.event.title)
        self.assertEqual(outlook_query['body'][0], details)
        self.assertEqual(
            outlook_query['startdt'][0],
            str(self.event.start.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S'))
        )
        self.assertEqual(
            outlook_query['enddt'][0], str(self.event.end.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S'))
        )

        self.assertTrue(
            links['ical'].startswith(reverse('event-ical', args=(self.event.pk, )))
        )

    def test_update(self):
        response = self.client.put(self.url, json.dumps(self.data), user=self.event.owner)

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

    def test_update_cancelled(self):
        self.event.initiative.states.submit()
        self.event.initiative.states.approve(save=True)
        self.event.refresh_from_db()
        self.event.states.cancel(save=True)

        response = self.client.put(self.url, json.dumps(self.data), user=self.event.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_deleted(self):
        self.event.states.delete(save=True)
        response = self.client.put(self.url, json.dumps(self.data), user=self.event.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_rejected(self):
        self.event.states.reject(save=True)
        response = self.client.put(self.url, json.dumps(self.data), user=self.event.owner)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(DEBUG=False)
    def test_update_event_image(self):

        file_path = './bluebottle/files/tests/files/test-image.png'
        with open(file_path) as test_file:
            response = self.client.post(
                reverse('image-list'),
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="some_file.jpg"',
                user=self.event.owner
            )

        file_data = json.loads(response.content)
        data = {
            'data': {
                'type': 'activities/events',
                'id': self.event.id,
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
        response = self.client.patch(self.url, json.dumps(data), user=self.event.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(
            data['data']['relationships']['image']['data']['id'],
            file_data['data']['id']
        )

        image = get_included(response, 'images')

        response = self.client.get(
            image['attributes']['links']['large'],
            user=self.event.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response['X-Accel-Redirect'].startswith(
                '/media/cache/'
            )
        )

    def test_missing_title(self):
        response = self.client.get(self.url, user=self.event.owner)
        data = response.json()['data']

        data['attributes']['title'] = ''

        response = self.client.put(
            self.url,
            data=json.dumps({'data': data}),
            user=self.event.owner,
            HTTP_X_DO_NOT_COMMIT=True
        )
        self.assertTrue(
            '/data/attributes/title' in (
                error['source']['pointer'] for error in response.json()['data']['meta']['required']
            )
        )


class EventTransitionTestCase(BluebottleTestCase):

    def setUp(self):
        super(EventTransitionTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory()
        self.manager = BlueBottleUserFactory()
        self.other_user = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create(activity_manager=self.manager)
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.event = EventFactory.create(owner=self.owner, initiative=self.initiative)

        self.event_url = reverse('event-detail', args=(self.event.id,))
        self.transition_url = reverse('activity-transition-list')

        self.review_data = {
            'data': {
                'type': 'activities/transitions',
                'attributes': {
                    'transition': 'delete',
                },
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'activities/events',
                            'id': self.event.pk
                        }
                    }
                }
            }
        }

    def test_check_event_transitions(self):

        response = self.client.get(
            self.event_url,
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(
            data['data']['meta']['transitions'],
            [
                {'available': True, 'name': 'submit', 'target': 'submitted'},
                {'available': True, 'name': 'delete', 'target': 'deleted'}
            ],
        )

    def test_delete_by_owner(self):
        # Owner can delete the event
        self.review_data['data']['attributes']['transition'] = 'delete'

        response = self.client.post(
            self.transition_url,
            json.dumps(self.review_data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        self.assertEqual(data['included'][0]['type'], 'activities/events')
        self.assertEqual(data['included'][0]['attributes']['status'], 'deleted')

    def test_delete_by_other_user(self):
        # Owner can delete the event

        self.review_data['data']['attributes']['transition'] = 'delete'

        response = self.client.post(
            self.transition_url,
            json.dumps(self.review_data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")

    def test_reject(self):
        self.review_data['data']['attributes']['transition'] = 'reject'
        response = self.client.post(
            self.transition_url,
            json.dumps(self.review_data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")

    def test_approve(self):
        self.review_data['data']['attributes']['transition'] = 'approve'
        response = self.client.post(
            self.transition_url,
            json.dumps(self.review_data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")


class ParticipantListTestCase(BluebottleTestCase):

    def setUp(self):
        super(ParticipantListTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.participant = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.event = EventFactory.create(owner=self.initiative.owner, initiative=self.initiative)

        self.participant_url = reverse('participant-list')
        self.event_url = reverse('event-detail', args=(self.event.pk, ))

        self.data = {
            'data': {
                'type': 'contributions/participants',
                'attributes': {},
                'relationships': {
                    'activity': {
                        'data': {
                            'id': self.event.pk,
                            'type': 'activities/events',
                        },
                    },
                }
            }
        }

    def test_create_participant(self):
        response = self.client.post(
            self.participant_url, json.dumps(self.data), user=self.participant
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['included'][0]['type'], 'activities/events')
        self.assertTrue(data['included'][0]['attributes']['is-follower'])

        response = self.client.get(
            self.event_url, user=self.participant
        )
        event_data = json.loads(response.content)
        self.assertEqual(
            len(event_data['data']['relationships']['contributions']['data']),
            1
        )
        self.assertEqual(
            event_data['data']['attributes']['stats']['count'],
            0
        )
        self.assertEqual(
            event_data['data']['attributes']['stats']['committed_count'],
            1
        )

        self.assertEqual(
            event_data['data']['relationships']['contributions']['data'][0]['id'],
            data['data']['id']
        )
        self.assertEqual(
            event_data['data']['relationships']['contributions']['data'][0]['type'],
            'contributions/participants'
        )
        self.assertTrue(event_data['data']['attributes']['is-follower'])

        participant_data = get_included(response, 'contributions/participants')

        self.assertTrue(participant_data['id'], self.participant.pk)
        self.assertTrue('meta' in participant_data)

    def test_create_twice(self):
        self.client.post(
            self.participant_url, json.dumps(self.data), user=self.participant
        )
        response = self.client.post(
            self.participant_url, json.dumps(self.data), user=self.participant
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            'must make a unique set' in response.json()['errors'][0]['detail']
        )


class ParticipantListFilterCase(BluebottleTestCase):
    def setUp(self):
        super(ParticipantListFilterCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.event = EventFactory(
            title='Test Title',
            status='open',
            start=(now() - timedelta(hours=5)),
            owner=self.initiative.owner,
            initiative=self.initiative,
            duration=4
        )

        ParticipantFactory.create_batch(3, activity=self.event, status='new')
        ParticipantFactory.create_batch(2, activity=self.event, status='cancelled')
        ParticipantFactory.create_batch(3, status='new')

        self.participant_url = reverse('participant-list')
        self.event_url = reverse('event-detail', args=(self.event.pk,))

    def test_list_all_participants(self):
        # Random user should only see successful participants (filtered by activity)
        response = self.client.get(
            self.participant_url, user=self.user
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)

    def test_list_participants(self):
        # Random user should only see successful participants (filtered by activity)
        response = self.client.get(
            self.participant_url, {'filter[activity.id]': self.event.id}, user=self.user
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_list_participants_event_owner(self):
        # Event host should see all participants (rejected / no show etc)
        response = self.client.get(
            self.participant_url, {'filter[activity.id]': self.event.id}, user=self.event.owner
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    def test_list_participants_by_event(self):
        # Requesting an event Random user should see successful participants
        response = self.client.get(self.event_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['contributions']), 3)

    def test_list_participants_by_event_owner(self):
        # Requesting an event event owner  should see successful all participants (rejected / no show etc)
        response = self.client.get(self.event_url, user=self.event.owner)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['contributions']), 5)

    def test_list_my_participation(self):
        response = self.client.get(
            self.participant_url, {'filter[user.id]': self.user.id}, user=self.user
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

        # Create 4 participant objects for this user for different events
        ParticipantFactory.create_batch(4, status='closed', user=self.user)
        response = self.client.get(
            self.participant_url, {'filter[user.id]': self.user.id}, user=self.user
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)

    def test_list_my_participation_by_event(self):
        # Filtering by user and activity user should only see
        # own participation for that event
        ParticipantFactory.create_batch(4, status='closed', user=self.user)
        ParticipantFactory.create(activity=self.event, status='closed', user=self.user)
        response = self.client.get(
            self.participant_url,
            {
                'filter[activity.id]': self.event.id,
                'filter[user.id]': self.user.id
            },
            user=self.user
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class ParticipantDetailTestCase(BluebottleTestCase):
    def setUp(self):
        super(ParticipantDetailTestCase, self).setUp()
        self.client = JSONAPITestClient()

        self.user = BlueBottleUserFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.event = EventFactory(
            title='Test Title',
            initiative=self.initiative,
            duration=4
        )
        self.participant = ParticipantFactory.create(activity=self.event)
        self.participant_url = reverse('participant-detail', args=(self.participant.pk, ))

    def test_possible_transitions(self):
        response = self.client.get(
            self.participant_url,
            user=self.participant.user
        )

        data = json.loads(response.content)
        self.assertEqual(
            [
                transition['name'] for transition in data['data']['meta']['transitions']
                if transition['available']
            ],
            ['withdraw']
        )

    def test_possible_transitions_other_user(self):
        response = self.client.get(
            self.participant_url,
            user=BlueBottleUserFactory.create()
        )

        data = json.loads(response.content)
        self.assertEqual(
            data['data']['meta']['transitions'], []
        )


class ParticipantTransitionTestCase(BluebottleTestCase):

    def setUp(self):
        super(ParticipantTransitionTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.url = reverse('event-list')
        self.participant_user = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)

        self.event = EventFactory.create(owner=self.initiative.owner, initiative=self.initiative)
        self.participant = ParticipantFactory.create(user=self.participant_user, activity=self.event)

        self.transition_url = reverse('participant-transition-list')
        self.event_url = reverse('event-detail', args=(self.event.pk, ))

        self.data = {
            'data': {
                'type': 'contributions/participant-transitions',
                'attributes': {
                    'transition': 'withdraw',
                },
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'contributions/participants',
                            'id': self.participant.pk
                        }
                    }
                }
            }
        }

    def test_withdraw(self):
        response = self.client.post(
            self.transition_url,
            json.dumps(self.data),
            user=self.participant_user
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['included'][1]['type'], 'contributions/participants')
        self.assertEqual(data['included'][1]['attributes']['status'], 'withdrawn')

        self.assertEqual(data['included'][0]['type'], 'activities/events')
        self.assertEqual(data['included'][0]['attributes']['is-follower'], False)

    def test_withdraw_other_user(self):
        response = self.client.post(
            self.transition_url,
            json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reapply(self):
        self.participant.states.withdraw(save=True)
        self.data['data']['attributes']['transition'] = 'reapply'

        response = self.client.post(
            self.transition_url,
            json.dumps(self.data),
            user=self.participant_user
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['included'][1]['type'], 'contributions/participants')
        self.assertEqual(data['included'][1]['attributes']['status'], 'new')

        self.assertEqual(data['included'][0]['type'], 'activities/events')
        self.assertEqual(data['included'][0]['attributes']['is-follower'], True)

    def test_reapply_other_user(self):
        self.participant.states.withdraw(save=True)
        self.data['data']['attributes']['transition'] = 'reapply'

        response = self.client.post(
            self.transition_url,
            json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
