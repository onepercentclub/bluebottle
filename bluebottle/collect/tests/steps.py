import json

from django.urls import reverse

from bluebottle.collect.models import CollectActivity


def api_create_collect_activity(
        test, initiative, attributes,
        request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = initiative.owner
    test.data = {
        'data': {
            'type': 'activities/collectactivities',
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
    url = reverse('collect-activity-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    if status_code == 201:
        return CollectActivity.objects.get(id=response.data['id'])


def api_update_collect_activity(
        test, activity, attributes,
        request_user=None, status_code=200, msg=None):
    if not request_user:
        request_user = activity.owner
    test.data = {
        'data': {
            'type': 'activities/collectactivities',
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
    url = reverse('collect-activity-detail', args=(activity.id,))
    response = test.client.patch(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    if status_code == 200:
        return CollectActivity.objects.get(id=response.data['id'])


def api_collect_activity_transition(
        test, activity, transition,
        request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = activity.owner
    test.data = {
        'data': {
            'type': 'activities/collect-activity-transitions',
            'attributes': {
                'transition': transition
            },
            'relationships': {
                'resource': {
                    'data': {
                        'type': 'activities/collectactivities',
                        'id': activity.pk
                    }
                }
            }
        }
    }
    url = reverse('collect-activities-transition-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)


def api_read_collect_activity(
        test, activity, request_user=None, status_code=200, msg=None):
    if not request_user:
        request_user = activity.owner
    url = reverse('collect-activity-detail', args=(activity.id,))
    response = test.client.get(url, user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    if status_code == 200:
        return CollectActivity.objects.get(id=response.data['id'])
