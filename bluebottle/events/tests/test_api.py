# coding=utf-8
import json
from datetime import timedelta
import urlparse

from django.urls import reverse
from django.utils.timezone import now, utc

import icalendar

from rest_framework import status

from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, get_included


class EventAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(EventAPITestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=['event']
        )

        self.client = JSONAPITestClient()
        self.url = reverse('event-list')
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory(owner=self.user)

    def test_create_event(self):
        start = now() + timedelta(days=21)
        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start_date': str(start.date()),
                    'start_time': str(start.time()),
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
        self.assertEqual(response.data['status'], 'in_review')
        self.assertEqual(response.data['title'], 'Beach clean-up Katwijk')

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
                    'start_date': str(start.date()),
                    'start_time': str(start.time()),
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
                    'start_date': str(start.date()),
                    'start_time': str(start.time()),
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
                    'start_date': str(start.date()),
                    'start_time': str(start.time()),
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
                    'start_date': str(start.date()),
                    'start_time': str(start.time()),
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

    def test_update_event(self):
        event = EventFactory.create(owner=self.user, title='Pollute Katwijk Beach')
        event_url = reverse('event-detail', args=(event.pk,))
        response = self.client.get(event_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Pollute Katwijk Beach')

        start = now() + timedelta(days=21)
        data = {
            'data': {
                'type': 'activities/events',
                'id': event.id,
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start_date': str(start.date()),
                    'start_time': str(start.time()),
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
        response = self.client.put(event_url, json.dumps(data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Beach clean-up Katwijk')

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
                    'start_date': str(start.date()),
                    'start_time': str(start.time()),
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
        self.assertEqual(response.data['status'], 'in_review')
        self.assertEqual(response.data['title'], 'Beach clean-up Katwijk')

    def test_create_event_not_initiator(self):
        another_user = BlueBottleUserFactory.create()
        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start_time': str((now() + timedelta(days=21)).time()),
                    'end_time': str((now() + timedelta(days=21, hours=4)).time()),
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

    def test_update_event_not_owner(self):
        event = EventFactory.create(title='Pollute Katwijk Beach')
        event_url = reverse('event-detail', args=(event.pk,))
        response = self.client.get(event_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Pollute Katwijk Beach')

        data = {
            'data': {
                'type': 'activities/events',
                'id': event.id,
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start_time': str(now() + timedelta(days=21)),
                    'end_time': str(now() + timedelta(days=21, hours=4)),
                    'registration_deadline': str(now() + timedelta(days=14)),
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
        response = self.client.put(event_url, json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_event_calendar_links(self):
        event = EventFactory.create(title='Pollute Katwijk Beach')
        event.description = u"Just kidding, we're going to clean it up of course 😉"
        event.save()
        event_url = reverse('event-detail', args=(event.pk,))
        response = self.client.get(event_url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        links = response.data['links']
        google_link = urlparse.urlparse(links['google'])
        google_query = urlparse.parse_qs(google_link.query)

        self.assertEqual(google_link.netloc, 'calendar.google.com')
        self.assertEqual(google_link.path, '/calendar/render')

        self.assertEqual(google_query['action'][0], 'TEMPLATE')
        self.assertEqual(google_query['location'][0], event.location.formatted_address)
        self.assertEqual(google_query['text'][0], event.title)
        self.assertEqual(google_query['uid'][0], 'test-event-{}'.format(event.pk))
        details = "Just kidding, we're going to clean it up of course \xf0\x9f\x98\x89\n" \
                  "http://testserver/en/initiatives/activities/details/" \
                  "event/{}/pollute-katwijk-beach".format(event.id)
        self.assertEqual(google_query['details'][0], details)
        self.assertEqual(
            google_query['dates'][0],
            u'{}/{}'.format(
                event.start.astimezone(utc).strftime('%Y%m%dT%H%M%SZ'),
                event.end.astimezone(utc).strftime('%Y%m%dT%H%M%SZ')
            )
        )

        outlook_link = urlparse.urlparse(links['outlook'])
        outlook_query = urlparse.parse_qs(outlook_link.query)

        self.assertEqual(outlook_link.netloc, 'outlook.live.com')
        self.assertEqual(outlook_link.path, '/owa/')

        self.assertEqual(outlook_query['rru'][0], 'addevent')
        self.assertEqual(outlook_query['path'][0], u'/calendar/action/compose&rru=addevent')
        self.assertEqual(outlook_query['location'][0], event.location.formatted_address)
        self.assertEqual(outlook_query['subject'][0], event.title)
        self.assertEqual(outlook_query['body'][0], details)
        self.assertEqual(
            outlook_query['startdt'][0], unicode(event.start.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S'))
        )
        self.assertEqual(
            outlook_query['enddt'][0], unicode(event.end.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S'))
        )

        self.assertEqual(
            links['ical'], reverse('event-ical', args=(event.pk, ))
        )


class EventIcalTestCase(BluebottleTestCase):
    def test_get(self):
        event = EventFactory.create(title='Pollute Katwijk Beach')
        event_url = reverse('event-ical', args=(event.pk,))

        response = self.client.get(event_url)

        self.assertEqual(response.get('content-type'), 'text/calendar')
        self.assertEqual(
            response.get('content-disposition'),
            'attachment; filename="{}.ics"'.format(event.slug)
        )

        calendar = icalendar.Calendar.from_ical(response.content)

        for ical_event in calendar.walk('vevent'):
            self.assertAlmostEqual(ical_event['dtstart'].dt, event.start, delta=timedelta(seconds=10))
            self.assertAlmostEqual(ical_event['dtend'].dt, event.end, delta=timedelta(seconds=10))
            self.assertEqual(str(ical_event['summary']), event.title)
            self.assertEqual(
                str(ical_event['description']),
                '{}\n{}'.format(event.description, event.get_absolute_url())
            )
            self.assertEqual(str(ical_event['url']), event.get_absolute_url())
            self.assertEqual(str(ical_event['organizer']), 'MAILTO:{}'.format(event.owner.email))


class EventValidationTestCase(BluebottleTestCase):
    def setUp(self):
        super(BluebottleTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.event = EventFactory.create(initiative=self.initiative, owner=self.owner)

        self.url = reverse('event-detail', args=(self.event.pk,))

    def get_data(self):
        return self.client.get(self.url, user=self.owner).json()['data']

    def test_missing_title(self):
        data = self.get_data()
        data['attributes']['title'] = ''

        response = self.client.put(
            self.url,
            data=json.dumps({'data': data}),
            user=self.owner,
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
        self.event = EventFactory.create(owner=self.owner, initiative=self.initiative)

        self.event_url = reverse('event-detail', args=(self.event.id,))
        self.transition_url = reverse('event-transition-list')
        self.review_transition_url = reverse('activity-review-transition-list')

        self.review_data = {
            'data': {
                'type': 'activities/review-transitions',
                'attributes': {
                    'transition': 'submit',
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
        self.data = {
            'data': {
                'type': 'event-transitions',
                'attributes': {
                    'transition': 'close',
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
        review_transitions = [
            {u'available': True, u'name': u'submit', u'target': u'submitted'},
            {u'available': False, u'name': u'close', u'target': u'closed'},
            {u'available': False, u'name': u'approve', u'target': u'approved'}
        ]
        transitions = [
            {u'available': False, u'name': u'reviewed', u'target': u'open'},
            {u'available': False, u'name': u'close', u'target': u'closed'}
        ]
        self.assertEqual(data['data']['meta']['review-transitions'], review_transitions)
        self.assertEqual(data['data']['meta']['transitions'], transitions)

    def test_submit_other_user(self):

        # Other user can't submit the event
        response = self.client.post(
            self.review_transition_url,
            json.dumps(self.review_data),
            user=self.other_user
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")

    def test_submit_owner(self):

        # Owner can submit the event
        response = self.client.post(
            self.review_transition_url,
            json.dumps(self.review_data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        self.assertEqual(data['included'][0]['type'], 'activities/events')
        self.assertEqual(data['included'][0]['attributes']['review-status'], 'submitted')

    def test_submit_manager(self):

        # Activity manager can submit the event
        response = self.client.post(
            self.review_transition_url,
            json.dumps(self.review_data),
            user=self.manager
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['included'][0]['type'], 'activities/events')
        self.assertEqual(data['included'][0]['attributes']['review-status'], 'submitted')

    def test_close(self):
        self.data['data']['attributes']['transition'] = 'close'
        response = self.client.post(
            self.transition_url,
            json.dumps(self.data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")

    def test_approve(self):
        self.data['data']['attributes']['transition'] = 'approve'
        response = self.client.post(
            self.transition_url,
            json.dumps(self.data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertEqual(data['errors'][0], "Transition is not available")


class ParticipantTestCase(BluebottleTestCase):

    def setUp(self):
        super(ParticipantTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.participant = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event = EventFactory.create(owner=self.initiative.owner, initiative=self.initiative)
        self.event.review_transitions.submit()
        self.event.save()

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
        participant_data = get_included(response, 'contributions/participants')

        self.assertTrue(participant_data['id'], self.participant.pk)
        self.assertTrue('meta' in participant_data)

    def test_create_participant_twice(self):
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

    def test_follow(self):
        self.client.post(
            self.participant_url, json.dumps(self.data), user=self.participant
        )

        response = self.client.get(
            self.event_url, user=self.participant
        )

        data = json.loads(response.content)

        self.assertTrue(data['data']['attributes']['is-follower'])

    def test_possible_transitions(self):
        response = self.client.post(
            self.participant_url, json.dumps(self.data), user=self.participant
        )
        create_data = json.loads(response.content)

        response = self.client.get(
            reverse('participant-detail', args=(create_data['data']['id'], )),
            user=self.participant
        )

        data = json.loads(response.content)
        self.assertEqual(
            [
                transition['name'] for transition in data['data']['meta']['transitions']
                if transition['available']
            ],
            ['initiate', 'withdraw', 'close']
        )

    def test_possible_transitions_other_user(self):
        response = self.client.post(
            self.participant_url, json.dumps(self.data), user=self.participant
        )
        create_data = json.loads(response.content)

        response = self.client.get(
            reverse('participant-detail', args=(create_data['data']['id'], )),
            user=BlueBottleUserFactory.create()
        )

        data = json.loads(response.content)
        self.assertEqual(
            [
                transition['name'] for transition in data['data']['meta']['transitions']
                if transition['available']],
            ['initiate', 'close']
        )


class ParticipantListFilterCase(BluebottleTestCase):

    def setUp(self):
        super(ParticipantListFilterCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event = EventFactory(
            title='Test Title',
            status='open',
            start_date=(now() - timedelta(hours=5)).date(),
            start_time=(now() - timedelta(hours=5)).time(),
            owner=self.initiative.owner,
            initiative=self.initiative,
            duration=4
        )

        ParticipantFactory.create_batch(3, activity=self.event, status='new')
        ParticipantFactory.create_batch(2, activity=self.event, status='closed')
        ParticipantFactory.create_batch(3, status='new')
        self.event.transitions.start()
        self.event.transitions.succeed()
        self.event.save()

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


class ParticipantTransitionTestCase(BluebottleTestCase):

    def setUp(self):
        super(ParticipantTransitionTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.url = reverse('event-list')
        self.participant_user = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()

        self.event = EventFactory.create(owner=self.initiative.owner, initiative=self.initiative)
        self.event.review_transitions.submit()
        self.event.save()
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

    def test_reapply(self):
        response = self.client.post(
            self.transition_url,
            json.dumps(self.data),
            user=self.participant_user
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {
            'data': {
                'type': 'contributions/participant-transitions',
                'attributes': {
                    'transition': 'reapply',
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

        response = self.client.post(
            self.transition_url,
            json.dumps(data),
            user=self.participant_user
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['included'][1]['type'], 'contributions/participants')
        self.assertEqual(data['included'][1]['attributes']['status'], 'new')

        self.assertEqual(data['included'][0]['type'], 'activities/events')
        self.assertEqual(data['included'][0]['attributes']['is-follower'], True)
