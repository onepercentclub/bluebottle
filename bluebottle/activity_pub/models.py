from django.db import models
from polymorphic.models import PolymorphicModel, PolymorphicManager

from bluebottle.members.models import Member


from django.contrib.contenttypes.models import ContentType


class ActivityPubModel(PolymorphicModel):
    def __init__(self, *args, **kwargs):

        ContentType.objects.clear_cache()
        super().__init__(*args, **kwargs)

    url = models.URLField(null=True)
    type = None


class Actor(ActivityPubModel):
    type = 'Actor'

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
    type = 'Person'
    name = models.TextField()

    member = models.OneToOneField(Member, null=True, on_delete=models.CASCADE)

    objects = PersonManager()


class Inbox(ActivityPubModel):
    type = 'Inbox'


class Outbox(ActivityPubModel):
    type = 'Outbox'


class Activity(ActivityPubModel):
    type = 'Activity'
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='activities')


class Follow(Activity):
    type = 'Follow'

    object = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE)


class PublicKey(ActivityPubModel):
    type = 'PublicKey'

    public_key_pem = models.TextField()
