import factory
from builtins import object
from datetime import timedelta
from django.utils import timezone

from bluebottle.activity_pub.models import (
    Organization, Inbox, Outbox, PublicKey, PrivateKey, Follow, Person, Place, Event,
    DoGoodEvent, SubEvent, Address, Image
)
from bluebottle.test.factory_models.organizations import OrganizationFactory as BluebottleOrganizationFactory


class PrivateKeyFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PrivateKey


class PublicKeyFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = PublicKey


class InboxFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Inbox


class OutboxFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Outbox


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Organization

    name = factory.Sequence(lambda n: 'ActivityPub Organization {0}'.format(n))
    summary = factory.Faker('text', max_nb_chars=200)
    content = factory.Faker('text', max_nb_chars=500)
    image = factory.SubFactory('bluebottle.activity_pub.tests.factories.ImageFactory')
    preferred_username = factory.Sequence(lambda n: 'activitypub_org_{0}'.format(n))

    inbox = factory.SubFactory(InboxFactory)
    outbox = factory.SubFactory(OutboxFactory)
    public_key = factory.SubFactory(PublicKeyFactory)
    organization = factory.SubFactory(BluebottleOrganizationFactory)


class PersonFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Person

    name = factory.Sequence(lambda n: 'Person {0}'.format(n))
    preferred_username = factory.Sequence(lambda n: 'person_{0}'.format(n))

    inbox = factory.SubFactory(InboxFactory)
    outbox = factory.SubFactory(OutboxFactory)
    public_key = factory.SubFactory(PublicKeyFactory)


class FollowFactory(factory.DjangoModelFactory):
    class Meta:
        model = Follow

    object = factory.SubFactory(OrganizationFactory)
    actor = factory.SubFactory(OrganizationFactory)


class AddressFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Address


class PlaceFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Place

    name = factory.Faker('company')
    latitude = factory.Faker('latitude')
    longitude = factory.Faker('longitude')

    address = factory.SubFactory(AddressFactory)


class EventFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Event

    name = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=500)
    image = factory.SubFactory('bluebottle.activity_pub.tests.factories.ImageFactory')
    start = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    end = factory.LazyFunction(lambda: timezone.now() + timedelta(days=8))
    organizer = factory.SubFactory(OrganizationFactory)
    place = factory.SubFactory(PlaceFactory)

    @factory.post_generation
    def with_duration(obj, create, extracted, **kwargs):
        """Add duration to make it a deadline activity type"""
        if extracted:
            obj.duration = timedelta(hours=4)
            obj.save()

    @factory.post_generation
    def with_subevents(obj, create, extracted, **kwargs):
        """Add subevents to make it a date activity type"""
        if extracted and create:
            # Create subevents
            EventFactory.create_batch(
                2,
                parent=obj,
                organizer=obj.organizer,
                place=obj.place,
                start=obj.start,
                end=obj.start + timedelta(hours=2)
            )


class SubEventFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = SubEvent

    start_time = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    end_time = factory.LazyFunction(lambda: timezone.now() + timedelta(days=8))
    duration = factory.LazyFunction(lambda: timedelta(hours=3))
    location = factory.SubFactory(PlaceFactory)


class ImageFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Image

    url = factory.Faker('image_url')


class DoGoodEventFactory(factory.DjangoModelFactory):
    @factory.post_generation
    def with_subevents(obj, create, extracted, **kwargs):
        """Add subevents to make it a date activity type"""
        if extracted and create:
            # Create subevents
            SubEventFactory.create_batch(
                2,
                parent=obj,
            )

    class Meta(object):
        model = DoGoodEvent

    name = factory.Faker('sentence', nb_words=4)
    summary = factory.Faker('text', max_nb_chars=500)
    image = factory.SubFactory(ImageFactory)
    organization = factory.SubFactory(OrganizationFactory)
