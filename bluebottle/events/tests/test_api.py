import json
from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
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
        data = {
            'data': {
                'type': 'activities/events',
                'attributes': {
                    'title': 'Beach clean-up Katwijk',
                    'start_time': str(now() + timedelta(days=21)),
                    'end_time': str(now() + timedelta(days=21, hours=4)),
                    'registration_deadline': str(now() + timedelta(days=14)),
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

        # Add an event with the same title should NOT return an error
        response = self.client.post(self.url, json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_event_disabled(self):
        self.settings.activity_types = ('funding', )
        self.settings.save()

        data = {
            'data': {
                'type': 'activities/events',
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
        response = self.client.post(self.url, json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_event(self):
        event = EventFactory.create(owner=self.user, title='Pollute Katwijk Beach')
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Beach clean-up Katwijk')

    def test_create_event_not_initiator(self):
        another_user = BlueBottleUserFactory.create()
        data = {
            'data': {
                'type': 'activities/events',
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


class EventValidationTestCase(BluebottleTestCase):
    def setUp(self):
        super(BluebottleTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.event = EventFactory.create(initiative=self.initiative, owner=self.owner)

        self.url = reverse('event-validations', args=(self.event.pk,))
        self.detail_url = reverse('event-detail', args=(self.event.pk,))

    def get_data(self):
        data = self.client.get(self.detail_url, user=self.owner).json()['data']
        data['type'] = 'event-validations'
        for key, value in data.pop('relationships').items():
            if value:
                data['attributes'][key] = value['data']

        return data

    def test_missing_title(self):
        data = self.get_data()
        data['attributes']['title'] = ''

        response = self.client.put(self.url, data=json.dumps({'data': data}), user=self.owner)
        self.assertEqual(
            response.json()['data']['attributes']['title'],
            [{'title': 'This field may not be blank.', 'code': 'blank'}]
        )

    def test_duplicate_missing_location(self):
        data = self.get_data()
        data['attributes']['location'] = None

        response = self.client.put(self.url, data=json.dumps({'data': data}), user=self.owner)
        self.assertEqual(
            response.json()['data']['attributes']['location'],
            [{'title': u'This field may not be null.', 'code': 'null'}]
        )


class EventTransitionTestCase(BluebottleTestCase):

    def setUp(self):
        super(EventTransitionTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.event = EventFactory.create(owner=self.owner, initiative=self.initiative)

        self.transition_url = reverse('event-transition-list')
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

    def test_close(self):
        response = self.client.post(
            self.transition_url,
            json.dumps(self.data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['included'][0]['type'], 'activities/events')
        self.assertEqual(data['included'][0]['attributes']['status'], 'closed')


class ParticipantTestCase(BluebottleTestCase):

    def setUp(self):
        super(ParticipantTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.participant = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
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
            'must make a unique set' in json.loads(response.content)['errors']['non_field_errors'][0]
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
            ['withdraw', 'close']
        )
        self.assertEqual(
            data['data']['meta']['transitions'][1]['conditions'],
            {u'event_is_successful': u'The event is not successful'}
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
            ['close']
        )
        self.assertEqual(
            data['data']['meta']['transitions'][1]['conditions'],
            {u'event_is_successful': u'The event is not successful'}
        )


class ParticipantListFilterCase(BluebottleTestCase):

    def setUp(self):
        super(ParticipantListFilterCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.event = EventFactory.create(owner=self.initiative.owner, initiative=self.initiative)
        ParticipantFactory.create_batch(3, activity=self.event, status='succeeded')
        ParticipantFactory.create_batch(2, activity=self.event, status='closed')
        ParticipantFactory.create_batch(3, status='succeeded')

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
