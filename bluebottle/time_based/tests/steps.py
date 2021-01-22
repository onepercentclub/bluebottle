import json

from django.urls import reverse
from rest_framework.status import HTTP_201_CREATED


def api_user_joins_activity(test, activity, supporter, request_user=None):
    if not request_user:
        request_user = supporter
    test.data = {
        'data': {
            'type': 'contributors/time-based/date-participants',
            'attributes': {
                'motiviation': 'I am great',
            },
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
    test.assertEqual(response.status_code, HTTP_201_CREATED)


def api_participant_transition(test, activity, supporter, transition, request_user=None):
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
    test.assertEqual(response.status_code, HTTP_201_CREATED)


def assert_participant_status(test, activity, supporter, status):
    return test.assertEqual(activity.contributors.filter(user=supporter).first().status, status)


def assert_status(test, model, status):
    model.refresh_from_db()
    return test.assertEqual(model.status, status)
