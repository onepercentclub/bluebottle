import json

from django.urls import reverse

from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.deeds.models import Deed


def api_create_deed(test, initiative, attributes,
                    request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = initiative.owner
    test.data = {
        'data': {
            'type': 'activities/deeds',
            'attributes': attributes,
            'relationships': {
                'initiative': {
                    'data': {
                        'type': 'initiatives',
                        'id': initiative.pk
                    }
                },
                'theme': {
                    'data': {
                        'type': 'themes',
                        'id': ThemeFactory.create().pk
                    }
                }
            }
        }
    }
    url = reverse('deed-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    if status_code == 201:
        return Deed.objects.get(id=response.data['id'])


def api_update_deed(test, activity, attributes,
                    request_user=None, status_code=200, msg=None):
    if not request_user:
        request_user = activity.owner
    test.data = {
        'data': {
            'type': 'activities/deeds',
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
    url = reverse('deed-detail', args=(activity.id,))
    response = test.client.patch(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    if status_code == 200:
        return Deed.objects.get(id=response.data['id'])


def api_deed_transition(test, activity, transition,
                        request_user=None, status_code=201, msg=None):
    if not request_user:
        request_user = activity.owner
    test.data = {
        'data': {
            'type': 'activities/deed-transitions',
            'attributes': {
                'transition': transition
            },
            'relationships': {
                'resource': {
                    'data': {
                        'type': 'activities/deeds',
                        'id': activity.pk
                    }
                }
            }
        }
    }
    url = reverse('deed-transition-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code, msg)


def api_read_deed(test, activity,
                  request_user=None, status_code=200, msg=None):
    if not request_user:
        request_user = activity.owner
    url = reverse('deed-detail', args=(activity.id,))
    response = test.client.get(url, user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    if status_code == 200:
        return Deed.objects.get(id=response.data['id'])
