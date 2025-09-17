from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicManager, PolymorphicModel

from bluebottle.members.models import Member
from bluebottle.organizations.models import Organization


class ActivityPubModel(PolymorphicModel):
    def __init__(self, *args, **kwargs):
        ContentType.objects.clear_cache()

        super().__init__(*args, **kwargs)

    url = models.URLField(null=True, unique=True)

    @property
    def pub_url(self):
        if self.url:
            return self.url
        else:
            model_name = self.__class__.__name__.lower()
            if model_name == 'puborganization':
                model_name = 'organization'
            return connection.tenant.build_absolute_url(
                reverse(f'json-ld:{model_name}', args=(str(self.pk),))
            )


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
        return self.name


class OrganizationManager(PolymorphicManager):

    def from_model(self, model):
        if not isinstance(model, Organization):
            raise TypeError("Model should be a organisation instance, not {}".format(type(model)))

        try:
            return model.puborganization
        except Organization.puborganization.RelatedObjectDoesNotExist:
            inbox = Inbox.objects.create()
            outbox = Outbox.objects.create()

            public_key = PublicKey.objects.create()
            logo = connection.tenant.build_absolute_url(model.logo.url) if model.logo else None

            return PubOrganization.objects.create(
                inbox=inbox,
                organization=model,
                outbox=outbox,
                public_key=public_key,
                name=model.name,
                image=logo,
                summary=model.description,
            )


class PubOrganization(Actor):
    name = models.CharField(max_length=300)
    summary = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    image = models.URLField(null=True, blank=True)

    organization = models.OneToOneField(
        Organization,
        null=True, on_delete=models.CASCADE
    )

    objects = OrganizationManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")


class Inbox(ActivityPubModel):
    pass


class Outbox(ActivityPubModel):
    pass


class PublicKey(ActivityPubModel):
    public_key_pem = models.TextField()


class Event(ActivityPubModel):
    name = models.CharField()
    description = models.TextField()
    image = models.URLField(null=True)
    start = models.DateTimeField(null=True)
    end = models.DateTimeField(null=True)
    duration = models.DurationField(null=True)
    organizer = models.ForeignKey(PubOrganization, on_delete=models.CASCADE)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="subevents",
    )

    activity = models.OneToOneField(
        "activities.Activity", null=True, on_delete=models.SET_NULL
    )

    slot_id = models.CharField(max_length=100, null=True, blank=True)

    @property
    def adopted(self):
        return self.activity is not None

    class Meta:
        verbose_name_plural = _("Shared activities")
        verbose_name = _("Shared activity")


class Activity(ActivityPubModel):
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='activities')


class Follow(Activity):
    object = models.ForeignKey(
        'activity_pub.Actor',
        verbose_name=_("Organisation"),
        on_delete=models.CASCADE
    )

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


class Announce(Activity):
    object = models.ForeignKey('activity_pub.Event', on_delete=models.CASCADE)

    @property
    def audience(self):
        return [self.object.organizer]
