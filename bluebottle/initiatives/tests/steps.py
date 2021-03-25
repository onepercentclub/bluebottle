import json

from bluebottle.initiatives.models import Initiative
from django.urls import reverse


def api_initiative_transition(test, initiative, transition, request_user=None, status_code=201):
    if not request_user:
        request_user = initiative.owner
    test.data = {
        'data': {
            'type': 'initiative-transitions',
            'attributes': {
                'transition': transition
            },
            'relationships': {
                'resource': {
                    'data': {
                        'type': 'initiatives',
                        'id': initiative.pk
                    }
                }
            }
        }
    }
    url = reverse('initiative-review-transition-list')
    response = test.client.post(url, json.dumps(test.data), user=request_user)
    test.assertEqual(response.status_code, status_code)


def api_read_initiative(test, initiative,
                        request_user=None, status_code=200, msg=None):
    if not request_user:
        request_user = initiative.owner
    url = reverse('initiative-detail', args=(initiative.id,))
    response = test.client.get(url, user=request_user)
    test.assertEqual(response.status_code, status_code, msg)
    if status_code == 200:
        return Initiative.objects.get(id=response.data['id'])
