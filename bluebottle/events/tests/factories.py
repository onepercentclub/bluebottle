import factory.fuzzy

from bluebottle.events.models import Event
from bluebottle.deeds.tests.factories import DeedFactory


class EventFactory(factory.DjangoModelFactory):
    class Meta():
        model = Event

    content_object = factory.SubFactory(DeedFactory)
