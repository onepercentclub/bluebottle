import json

from behave import given, when, then
from django.urls import reverse

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.time_based.tests.factories import DateActivityFactory


@given('A user interacts with the API')
def authenticated_user(context):
    context.user = BlueBottleUserFactory.create()


@given('There is an activity on a date')
def have_an_activity(context):
    context.activity = DateActivityFactory.create()


@when('User joins activity')
def join_activity(context):
    url = reverse('date-participant-list')
    data = {
        'data': {
            'type': 'contributors/time-based/date-participants',
            'attributes': {
                'motiviation': 'I am great',
            },
            'relationships': {
                'activity': {
                    'data': {
                        'type': 'activities/time-based/dates',
                        'id': context.activity.pk
                    }
                }
            }
        }
    }
    print(context.client.post(url, json.dumps(data), user=context.user))


@then('User is part of the activity')
def check_user_part_of_activity(context):
    print(context.activity.contributors)
    print(context.user)
    return context.user in [p.user for p in context.activity.contributors.all()]
