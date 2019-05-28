import json
from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class EventTestCase(BluebottleTestCase):

    def setUp(self):
        super(EventTestCase, self).setUp()
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
                'type': 'events',
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
        self.assertEqual(response.data['status'], 'open')
        self.assertEqual(response.data['title'], 'Beach clean-up Katwijk')

        # Add an event with the same title should NOT return an error
        response = self.client.post(self.url, json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_event_disabled(self):
        self.settings.activity_types = ('funding', )
        self.settings.save()

        data = {
            'data': {
                'type': 'events',
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
                'type': 'events',
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
                'type': 'events',
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
                'type': 'events',
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
                            'type': 'events',
                            'id': self.event.pk
                        }
                    }
                }
            }
        }

    def test_submit(self):
        response = self.client.post(
            self.transition_url,
            json.dumps(self.data),
            user=self.owner
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content)

        self.assertEqual(data['included'][0]['type'], 'events')
        self.assertEqual(data['included'][0]['attributes']['status'], 'closed')


class ParticipantTestCase(BluebottleTestCase):

    def setUp(self):
        super(ParticipantTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.participant = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create()
        self.event = EventFactory.create(owner=self.initiative.owner, initiative=self.initiative)

        self.participant_url = reverse('participant-list')
        self.event_url = reverse('event-detail', args=(self.event.pk, ))

        self.data = {
            'data': {
                'type': 'participants',
                'attributes': {},
                'relationships': {
                    'activity': {
                        'data': {
                            'id': self.event.pk,
                            'type': 'events',
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

        self.assertEqual(data['data']['attributes']['status'], 'going')
        self.assertEqual(data['included'][0]['type'], 'events')
        self.assertTrue(data['included'][0]['attributes']['is-follower'])

    def test_follow(self):
        self.client.post(
            self.participant_url, json.dumps(self.data), user=self.participant
        )

        response = self.client.get(
            self.event_url, user=self.participant
        )

        data = json.loads(response.content)

        self.assertTrue(data['data']['attributes']['is-follower'])


class ParticipantTransitionTestCase(BluebottleTestCase):

    def setUp(self):
        super(ParticipantTransitionTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.url = reverse('event-list')
        self.participant_user = BlueBottleUserFactory()

        self.initiative = InitiativeFactory.create()
        self.event = EventFactory.create(owner=self.initiative.owner, initiative=self.initiative)
        self.participant = ParticipantFactory.create(user=self.participant_user, activity=self.event)

        self.transition_url = reverse('participant-transition-list')
        self.event_url = reverse('event-detail', args=(self.event.pk, ))

        self.data = {
            'data': {
                'type': 'participant-transitions',
                'attributes': {
                    'transition': 'withdraw',
                },
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'participants',
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

        self.assertEqual(data['included'][1]['type'], 'participants')
        self.assertEqual(data['included'][1]['attributes']['status'], 'withdrawn')

        self.assertEqual(data['included'][0]['type'], 'events')
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
                'type': 'participant-transitions',
                'attributes': {
                    'transition': 'go',
                },
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'participants',
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

        self.assertEqual(data['included'][1]['type'], 'participants')
        self.assertEqual(data['included'][1]['attributes']['status'], 'going')

        self.assertEqual(data['included'][0]['type'], 'events')
        self.assertEqual(data['included'][0]['attributes']['is-follower'], True)
