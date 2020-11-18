from datetime import timedelta, date

import factory.fuzzy
from django.utils.timezone import now

from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, Duration
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


class DateActivityFactory(TimeBasedFactory):
    class Meta:
        model = DateActivity

    start = (now() + timedelta(weeks=4))
    duration = timedelta(hours=2)


class PeriodActivityFactory(TimeBasedFactory):
    class Meta:
        model = PeriodActivity

    deadline = date.today() + timedelta(weeks=4)
    duration = timedelta(hours=20)
    duration_period = 'overall'
    is_online = False

    start = (now() + timedelta(weeks=1)).date()


class DateParticipantFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = DateParticipant

    activity = factory.SubFactory(DateActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)


class PeriodParticipantFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PeriodParticipant

    activity = factory.SubFactory(DateActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)


class DurationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Duration

    contributor = factory.SubFactory(PeriodParticipantFactory)

    value = timedelta(hours=20)

    start = now() + timedelta(weeks=1)
    end = now() + timedelta(weeks=2)
