from django.utils import translation
from django.template.loader import get_template

from bluebottle.activities.tasks import get_matching_activities
from bluebottle.members.models import Member
import logging


from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.time_based.tests.factories import DateActivityFactory, PeriodActivityFactory

from bluebottle.activities.messages import MatchingActivitiesNotification
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


def run(*args):
    for tenant in Client.objects.filter(name='GoodUp Demo'):
        with LocalTenant(tenant, clear_tenant=True):

            translation.activate('en')

            user = Member.objects.get(pk=112)
            activities = get_matching_activities(user)

            notification = MatchingActivitiesNotification(user)
            context = notification.get_context(user, activities=activities)
            print(
                get_template(
                    'mails/{0}.html'.format(notification.template)
                ).render(context)
            )

