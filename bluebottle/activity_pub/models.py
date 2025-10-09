from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicManager, PolymorphicModel

from bluebottle.members.models import Member
from bluebottle.organizations.models import Organization as BluebottleOrganization
from bluebottle.utils.models import ChoiceItem, DjangoChoices


class ActivityPubModel(PolymorphicModel):
    def __init__(self, *args, **kwargs):
        ContentType.objects.clear_cache()
        super().__init__(*args, **kwargs)

    iri = models.URLField(null=True, unique=True)

    @property
    def is_local(self):
        return self.iri is None

    @property
    def pub_url(self):
        if self.iri:
            return self.iri
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
        if not self.iri and not self.private_key:

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


class Address(ActivityPubModel):
    street_address = models.CharField(max_length=1000, null=True)
    postal_code = models.CharField(max_length=1000, null=True)

    address_locality = models.CharField(max_length=1000, null=True)
    address_region = models.CharField(max_length=1000, null=True)
    address_country = models.CharField(max_length=1000, null=True)


class Place(ActivityPubModel):
    name = models.CharField(max_length=1000)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.SET_NULL)


class Image(ActivityPubModel):
    name = models.CharField(max_length=1000, null=True)
    url = models.URLField(null=True)


class Event(ActivityPubModel):
    name = models.CharField()
    summary = models.TextField()
    image = models.ForeignKey(Image, null=True, on_delete=models.SET_NULL)
    activity = models.OneToOneField(
        "activities.Activity", null=True, on_delete=models.SET_NULL
    )

    @property
    def source(self):
        publish = Publish.objects.filter(object=self).first()
        if publish:
            return publish.actor

    @property
    def adopted_activity(self):
        return self.adopted_activities.first()

    @property
    def adopted(self):
        return self.adopted_activity is not None

    def __str__(self):
        return self.name

    @property
    def pub_url(self):
        if self.iri:
            return self.iri
        else:
            model_name = self.get_real_instance_class().__name__
            import re
            dashed_name = re.sub(r'(?<!^)(?=[A-Z])', '-', model_name).lower()
            return connection.tenant.build_absolute_url(
                reverse(f'json-ld:{dashed_name}', args=(str(self.pk),))
            )

    class Meta:
        verbose_name = _("Shared activity")
        verbose_name_plural = _("Shared activities")


class PublishedActivity(Event):

    class Meta:
        proxy = True
        verbose_name = _("Published activity")
        verbose_name_plural = _("Publihed activities")


class ReceivedActivity(Event):

    class Meta:
        proxy = True
        verbose_name = _("Received activity")
        verbose_name_plural = _("Received activities")


class GoodDeed(Event):
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    class Meta:
        verbose_name = _("Deed")
        verbose_name_plural = _("Deeds")


class CrowdFunding(Event):
    target = models.DecimalField(decimal_places=2, max_digits=10)
    target_currency = models.CharField(max_length=3)

    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    location = models.ForeignKey(Place, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Funding")
        verbose_name_plural = _("Funding")


class EventAttendanceModeChoices(DjangoChoices):
    online = ChoiceItem('OnlineEventAttendanceMode')
    offline = ChoiceItem('OfflineEventAttendanceMode')


class SubEvent(ActivityPubModel):
    name = models.CharField(null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    location = models.ForeignKey(Place, null=True, blank=True, on_delete=models.CASCADE)
    duration = models.DurationField(null=True)
    event_attendance_mode = models.CharField(
        choices=EventAttendanceModeChoices.choices,
        null=True
    )
    parent = models.ForeignKey(
        'activity_pub.DoGoodEvent',
        null=True,
        on_delete=models.CASCADE,
        related_name='sub_events'
    )
    slot = models.ForeignKey('time_based.DateActivitySlot', null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Sub event")
        verbose_name_plural = _("Sub events")


class DoGoodEvent(Event):
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    location = models.ForeignKey(Place, null=True, blank=True, on_delete=models.CASCADE)
    duration = models.DurationField(null=True)
    event_attendance_mode = models.CharField(
        choices=EventAttendanceModeChoices.choices,
        null=True
    )

    class Meta(Event.Meta):
        verbose_name = _('Date activity')
        verbose_name_plural = _('Date activities')


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
        for publish in self.object.publish_set.all():
            for follow in publish.actor.follow_set.all():
                yield follow.object.inbox
