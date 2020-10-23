from datetime import timedelta

import factory.fuzzy
from django.utils.timezone import now

from bluebottle.time_based.models import (
    OnADateActivity, WithADeadlineActivity, OngoingActivity,
    Application
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.factory_models.tasks import SkillFactory


class TimeBasedFactory(factory.DjangoModelFactory):
    title = factory.Faker('sentence')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    capacity = 10
    is_online = False
    review = False

    expertise = factory.SubFactory(SkillFactory)
    location = factory.SubFactory(GeolocationFactory)
    registration_deadline = (now() + timedelta(weeks=2)).date()


class OnADateActivityFactory(TimeBasedFactory):
    class Meta:
        model = OnADateActivity

    start = (now() + timedelta(weeks=4))
    duration = 2


class WithADeadlineActivityFactory(TimeBasedFactory):
    class Meta:
        model = WithADeadlineActivity

    deadline = (now() + timedelta(weeks=4))
    duration = 20
    duration_period = 'overall'


class OngoingActivityFactory(TimeBasedFactory):
    class Meta:
        model = OngoingActivity

    duration = 20
    duration_period = 'overall'


class ApplicationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Application

    activity = factory.SubFactory(OnADateActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
