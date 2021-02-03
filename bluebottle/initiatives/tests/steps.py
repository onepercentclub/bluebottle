import json

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
