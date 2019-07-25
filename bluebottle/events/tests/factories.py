from datetime import timedelta

import factory.fuzzy
from django.utils.timezone import now

from bluebottle.events.models import Event, Participant
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory


class EventFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = Event

    title = factory.Faker('sentence')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    capacity = 10
    automatically_accept = True
    is_online = False

    registration_deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=2))
    start_time = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=4))
    end_time = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=5))

    location = factory.SubFactory(GeolocationFactory)


class ParticipantFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Participant

    activity = factory.SubFactory(EventFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
