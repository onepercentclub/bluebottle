from urllib.parse import urlparse

from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.urls import reverse
from django_quill.fields import QuillField
from polymorphic.models import PolymorphicManager, PolymorphicModel

from bluebottle.clients.models import Client
from bluebottle.deeds.models import Deed
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.members.models import Member


class ActivityPubModel(PolymorphicModel):
    def __init__(self, *args, **kwargs):

        ContentType.objects.clear_cache()
        super().__init__(*args, **kwargs)

    url = models.URLField(null=True)

    @property
    def platform(self):
        if not self.url:
            return None

        parsed_url = urlparse(self.url)
        domain_url = parsed_url.netloc.split(":")[0]
        tenant = Client.objects.filter(domain_url=domain_url).first()
        return tenant.name if tenant else None


class Actor(ActivityPubModel):
    inbox = models.ForeignKey('activity_pub.Inbox', on_delete=models.CASCADE)
    outbox = models.ForeignKey('activity_pub.Outbox', on_delete=models.CASCADE)
    public_key = models.ForeignKey('activity_pub.PublicKey', on_delete=models.CASCADE)


class PersonManager(PolymorphicManager):
    def from_model(self, model):
        if not isinstance(model, Member):
            raise TypeError("Model should be a member instance")

        try:
            return model.person
        except Member.person.RelatedObjectDoesNotExist:
            inbox = Inbox.objects.create()
            outbox = Outbox.objects.create()

            public_key = PublicKey.objects.create()

            return Person.objects.create(
                inbox=inbox,
                member=model,
                outbox=outbox,
                public_key=public_key,
                name=model.full_name
            )


class Person(Actor):
    name = models.TextField()

    member = models.OneToOneField(Member, null=True, on_delete=models.CASCADE)

    objects = PersonManager()

    def __str__(self):
        if self.platform:
            return self.name + " @ " + self.platform
        return self.name


class Inbox(ActivityPubModel):
    pass


class Outbox(ActivityPubModel):
    pass


class PublicKey(ActivityPubModel):
    public_key_pem = models.TextField()


class EventManager(PolymorphicManager):
    def from_model(self, model):
        if not isinstance(model, Deed):
            raise TypeError("Model should be a member instance")

        try:
            return model.event
        except Deed.event.RelatedObjectDoesNotExist:
            if model.image:
                image_url = reverse('activity-image', args=(str(model.pk), ORIGINAL_SIZE))
            elif model.initiative and model.initiative.image:
                image_url = reverse('initiative-image', args=(str(model.initiative.pk), ORIGINAL_SIZE))

            return Event.objects.create(
                start_date=model.start,
                end_date=model.end,
                organizer=Person.objects.from_model(model.owner),
                name=model.title,
                description=model.description,
                image=connection.tenant.build_absolute_url(image_url) if image_url else None,
                activity=model
            )


class Event(ActivityPubModel):
    name = models.CharField()
    description = QuillField()
    image = models.URLField(null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    organizer = models.ForeignKey(Person, on_delete=models.CASCADE)

    activity = models.OneToOneField(Deed, null=True, on_delete=models.CASCADE)
    objects = EventManager()


class Activity(ActivityPubModel):
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='activities')


class Follow(Activity):
    object = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE)

    @property
    def audience(self):
        return [self.object]


class Accept(Activity):
    object = models.ForeignKey('activity_pub.Follow', on_delete=models.CASCADE)

    @property
    def audience(self):
        return [self.object.actor]


class Publish(Activity):
    object = models.ForeignKey('activity_pub.Event', on_delete=models.CASCADE)

    @property
    def audience(self):
        # All followers of the actor
        for follow in self.actor.follow_set.all():
            yield follow.actor.inbox
