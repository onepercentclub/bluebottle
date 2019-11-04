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
    status = 'in_review'
    review_status = 'draft'

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    capacity = 10
    automatically_accept = True
    is_online = False

    start_date = (now() + timedelta(weeks=4)).date()
    start_time = (now() + timedelta(weeks=4)).time()
    duration = 100

    location = factory.SubFactory(GeolocationFactory)


class ParticipantFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Participant

    activity = factory.SubFactory(EventFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
