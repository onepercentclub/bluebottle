import json

from django.urls import reverse

from bluebottle.time_based.models import DateActivity, DateActivitySlot


def api_create_date_activity(test, initiative, attributes,
                             request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = initiative.owner
    test.data = {
        'data': {
            'type': 'activities/time-based/dates',
            'attributes': attributes,
            'relationships': {
                'initiative': {
                    'data': {
                        'type': 'initiatives',
                        'id': initiative.pk
                    }
                }
            }
        }
    }
    url = reverse('date-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    if status_code == 201:
        return DateActivity.objects.get(id=response.data['id'])


def api_update_date_activity(test, activity, attributes,
                             request_user=None, status_code=200, msg=None):
    if not request_user:
        request_user = activity.owner
    test.data = {
        'data': {
            'type': 'activities/time-based/dates',
            'id': activity.id,
            'attributes': attributes,
            'relationships': {
                'initiative': {
                    'data': {
                        'type': 'initiatives',
                        'id': activity.initiative.pk
                    }
                }
            }
        }
    }
    url = reverse('date-detail', args=(activity.id,))
    response = test.client.patch(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    if status_code == 200:
        return DateActivity.objects.get(id=response.data['id'])


def api_activity_transition(test, activity, transition,
                            request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = activity.owner
    test.data = {
        'data': {
            'type': 'activities/time-based/date-transitions',
            'attributes': {
                'transition': transition
            },
            'relationships': {
                'resource': {
                    'data': {
                        'type': 'activities/time-based/dates',
                        'id': activity.pk
                    }
                }
            }
        }
    }
    url = reverse('date-transition-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)


def api_create_date_slot(test, activity, attributes,
                         request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = activity.owner
    test.data = {
        'data': {
            'type': 'activities/time-based/date-slots',
            'attributes': attributes,
            'relationships': {
                'activity': {
                    'data': {
                        'type': 'activities/time-based/dates',
                        'id': activity.pk
                    }
                }
            }
        }
    }
    url = reverse('date-slot-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    return DateActivitySlot.objects.get(id=response.data['id'])


def api_update_date_slot(test, slot, attributes,
                         request_user=None, status_code=200, msg=None):
    if not request_user:
        request_user = slot.activity.owner
    test.data = {
        'data': {
            'type': 'activities/time-based/date-slots',
            'id': slot.id,
            'attributes': attributes,
            'relationships': {
                'activity': {
                    'data': {
                        'type': 'activities/time-based/dates',
                        'id': slot.activity.pk
                    }
                }
            }
        }
    }
    url = reverse('date-slot-detail', args=(slot.id,))
    response = test.client.patch(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    return DateActivitySlot.objects.get(id=response.data['id'])


def api_user_joins_activity(test, activity, supporter,
                            request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = supporter
    test.data = {
        'data': {
            'type': 'contributors/time-based/date-participants',
            'relationships': {
                'activity': {
                    'data': {
                        'type': 'activities/time-based/dates',
                        'id': activity.pk
                    }
                }
            }
        }
    }
    url = reverse('date-participant-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)


def api_user_joins_period_activity(
        test, activity, supporter,
        request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = supporter
    test.data = {
        'data': {
            'type': 'contributors/time-based/period-participants',
            'relationships': {
                'activity': {
                    'data': {
                        'type': 'activities/time-based/periods',
                        'id': activity.pk
                    }
                }
            }
        }
    }
    url = reverse('period-participant-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)


def api_user_joins_slot(test, slot, supporter, request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = supporter
    participant = slot.activity.contributors.filter(user=supporter).get()
    test.data = {
        'data': {
            'type': 'contributors/time-based/slot-participants',
            'relationships': {
                'slot': {
                    'data': {
                        'type': 'activities/time-based/date-slots',
                        'id': slot.id
                    },
                },
                'participant': {
                    'data': {
                        'type': 'contributors/time-based/date-participants',
                        'id': participant.id
                    },
                },
            }
        }
    }
    url = reverse('slot-participant-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)


def api_participant_transition(test, activity, supporter, transition,
                               request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = supporter
    participant = activity.contributors.filter(user=supporter).get()
    test.data = {
        'data': {
            'type': 'contributors/time-based/date-participant-transitions',
            'attributes': {
                'transition': transition
            },
            'relationships': {
                'resource': {
                    'data': {
                        'type': 'contributors/time-based/date-participants',
                        'id': participant.pk
                    }
                }
            }
        }
    }
    url = reverse('date-participant-transition-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)


def api_slot_participant_transition(test, slot, supporter, transition,
                                    request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = supporter
    slot_participant = slot.slot_participants.filter(participant__user=supporter).get()
    test.data = {
        'data': {
            'type': 'contributors/time-based/slot-participant-transitions',
            'attributes': {
                'transition': transition
            },
            'relationships': {
                'resource': {
                    'data': {
                        'type': 'contributors/time-based/slot-participants',
                        'id': slot_participant.pk
                    }
                }
            }
        }
    }
    url = reverse('slot-participant-transition-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)


def assert_participant_status(test, activity, supporter, status, msg=None):
    participant = activity.contributors.filter(user=supporter).first()
    return test.assertEqual(participant.status, status, msg)


def assert_slot_participant_status(test, slot, supporter, status, msg=None):
    slot_participant = slot.slot_participants.filter(participant__user=supporter).first()
    return test.assertEqual(slot_participant.status, status, msg)


def assert_not_participant(test, activity, supporter, msg=None):
    participant = activity.contributors.filter(user=supporter).first()
    return test.assertIsNone(participant, msg)


def assert_not_slot_participant(test, slot, supporter, msg=None):
    slot_participant = slot.slot_participants.filter(participant__user=supporter).first()
    return test.assertIsNone(slot_participant, msg)


def assert_status(test, model, status, msg=None):
    model.refresh_from_db()
    return test.assertEqual(model.status, status, msg)
