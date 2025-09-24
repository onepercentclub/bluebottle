from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicManager, PolymorphicModel

from bluebottle.members.models import Member
from bluebottle.organizations.models import Organization as BluebottleOrganization


class ActivityPubModel(PolymorphicModel):
    def __init__(self, *args, **kwargs):
        ContentType.objects.clear_cache()
        super().__init__(*args, **kwargs)

    url = models.URLField(null=True, unique=True)

    @property
    def is_local(self):
        return self.url is None

    @property
    def pub_url(self):
        if self.url:
            return self.url
        else:
            model_name = self.__class__.__name__.lower()
            return connection.tenant.build_absolute_url(
                reverse(f'json-ld:{model_name}', args=(str(self.pk),))
            )


class Actor(ActivityPubModel):
    inbox = models.ForeignKey('activity_pub.Inbox', on_delete=models.CASCADE)
    outbox = models.ForeignKey('activity_pub.Outbox', on_delete=models.CASCADE)
    public_key = models.ForeignKey('activity_pub.PublicKey', on_delete=models.CASCADE)
    preferred_username = models.CharField(blank=True, null=True)

    @property
    def webfinger_uri(self):
        if self.preferred_username:
            return f'acct:{self.preferred_username}@{connection.tenant.domain_url}'

    def __str__(self):
        try:
            return self.person.name
        except Person.DoesNotExist:
            pass
        try:
            return self.organization.name
        except (Organization.DoesNotExist, AttributeError):
            pass
        return self.preferred_username


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
        if not isinstance(model, BluebottleOrganization):
            raise TypeError("Model should be a organisation instance, not {}".format(type(model)))

        try:
            return model.activity_pub_organization
        except BluebottleOrganization.activity_pub_organization.RelatedObjectDoesNotExist:
            inbox = Inbox.objects.create()
            outbox = Outbox.objects.create()

            public_key = PublicKey.objects.create()
            logo = connection.tenant.build_absolute_url(model.logo.url) if model.logo else None

            return Organization.objects.create(
                inbox=inbox,
                organization=model,
                outbox=outbox,
                public_key=public_key,
                name=model.name,
                image=logo,
                summary=model.description,
                preferred_username=model.slug
            )


class Organization(Actor):
    name = models.CharField(max_length=300)
    summary = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    image = models.URLField(null=True, blank=True)

    organization = models.OneToOneField(
        BluebottleOrganization,
        null=True,
        on_delete=models.CASCADE,
        related_name='activity_pub_organization'
    )

    objects = OrganizationManager()

    class Meta:
        verbose_name = _("Platform")
        verbose_name_plural = _("Platforms")

    def __str__(self):
        return self.name


class Inbox(ActivityPubModel):
    pass


class Outbox(ActivityPubModel):
    pass


class PrivateKey(models.Model):
    private_key_pem = models.TextField()


class PublicKey(ActivityPubModel):
    public_key_pem = models.TextField()
    private_key = models.ForeignKey(PrivateKey, null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.url and not self.private_key:

            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')

            self.private_key = PrivateKey.objects.create(
                private_key_pem=private_key_pem

            )
            self.public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

        super().save(*args, **kwargs)


class Place(ActivityPubModel):
    name = models.CharField(max_length=1000)
    latitude = models.CharField(max_length=1000)
    longitude = models.CharField(max_length=1000)

    street_address = models.CharField(max_length=1000)
    postal_code = models.CharField(max_length=1000)

    locality = models.CharField(max_length=1000)
    region = models.CharField(max_length=1000)
    country = models.CharField(max_length=1000)
    country_code = models.CharField(max_length=5)

    mapbox_id = models.CharField(max_length=1000)


class Event(ActivityPubModel):
    name = models.CharField()
    description = models.TextField()
    image = models.URLField(null=True)
    start = models.DateTimeField(null=True)
    end = models.DateTimeField(null=True)
    duration = models.DurationField(null=True)
    organizer = models.ForeignKey(Organization, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, null=True, blank=True, on_delete=models.SET_NULL)  # Add this field

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
    def activity_type(self):
        if self.subevents.exists():
            return "date"
        if self.duration:
            return "deadline"
        return "deed"

    @property
    def adopted(self):
        return self.activity is not None

    class Meta:
        verbose_name_plural = _("Shared activities")
        verbose_name = _("Shared activity")


class Activity(ActivityPubModel):
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='activities')

    def save(self, *args, **kwargs):
        from bluebottle.activity_pub.utils import get_platform_actor

        if not hasattr(self, 'actor'):
            self.actor = get_platform_actor()

        super().save(*args, **kwargs)


class Follow(Activity):
    object = models.ForeignKey(
        'activity_pub.Actor',
        verbose_name=_("Platform"),
        on_delete=models.CASCADE
    )

    @property
    def audience(self):
        return [self.object]


class Follower(Follow):
    class Meta:
        proxy = True
        verbose_name = _('Follower')
        verbose_name_plural = _('Followers')

    def __str__(self):
        return str(self.actor)


class Following(Follow):
    class Meta:
        proxy = True
        verbose_name = _('Following')
        verbose_name_plural = _('Following')

    def __str__(self):
        try:
            return str(self.object)
        except Actor.DoesNotExist:
            return "-"


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
        for follow in self.actor.follow_set.filter(accept__isnull=False):
            yield follow.actor.inbox


class Announce(Activity):
    object = models.ForeignKey('activity_pub.Event', on_delete=models.CASCADE)

    @property
    def audience(self):
        return [self.object.organizer]
