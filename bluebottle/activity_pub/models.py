from urllib.parse import urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from django.contrib.contenttypes.models import ContentType
from django.db import models, connection
from django.urls import reverse, resolve
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicManager, PolymorphicModel

from bluebottle.members.models import Member
from bluebottle.organizations.models import Organization as BluebottleOrganization
from bluebottle.utils.models import ChoiceItem, DjangoChoices


class ActivityPubManager(PolymorphicManager):
    def from_iri(self, iri):
        from bluebottle.activity_pub.utils import is_local

        if is_local(iri):
            resolved = resolve(urlparse(iri).path)
            return self.get(pk=resolved.kwargs['pk'])
        else:
            return self.get(iri=iri)


class ActivityPubModel(PolymorphicModel):
    def __init__(self, *args, **kwargs):
        ContentType.objects.clear_cache()
        super().__init__(*args, **kwargs)

    iri = models.URLField(null=True, unique=True)

    objects = ActivityPubManager()

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

    class Meta:
        verbose_name = _("GoodUp Connect object")
        verbose_name_plural = _("GoodUp Connect objects")


class Actor(ActivityPubModel):
    inbox = models.ForeignKey('activity_pub.Inbox', on_delete=models.SET_NULL, null=True, blank=True)
    outbox = models.ForeignKey('activity_pub.Outbox', on_delete=models.SET_NULL, null=True, blank=True)
    public_key = models.ForeignKey('activity_pub.PublicKey', on_delete=models.SET_NULL, null=True, blank=True)
    preferred_username = models.CharField(blank=True, null=True)

    @property
    def follow(self):
        follow = Follow.objects.filter(object=self).first()
        return follow

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


class PersonManager(ActivityPubManager):
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


class OrganizationManager(ActivityPubManager):

    def from_model(self, model):
        if not isinstance(model, BluebottleOrganization):
            raise TypeError("Model should be a organisation instance, not {}".format(type(model)))

        try:
            return model.activity_pub_organization
        except BluebottleOrganization.activity_pub_organization.RelatedObjectDoesNotExist:
            inbox = Inbox.objects.create()
            outbox = Outbox.objects.create()

            public_key = PublicKey.objects.create()
            logo_url = connection.tenant.build_absolute_url(model.logo.url) if model.logo else None

            return Organization.objects.create(
                inbox=inbox,
                organization=model,
                outbox=outbox,
                public_key=public_key,
                name=model.name,
                logo=Image.objects.create(
                    url=logo_url,
                    name=model.logo.name
                ) if logo_url else None,
                summary=model.description,
                preferred_username=model.slug
            )


class Image(ActivityPubModel):
    name = models.CharField(max_length=1000, null=True)
    url = models.URLField(null=True)


class Organization(Actor):
    name = models.CharField(max_length=300)
    summary = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)

    image = models.ForeignKey(Image, null=True, on_delete=models.SET_NULL)
    logo = models.ForeignKey(Image, null=True, on_delete=models.SET_NULL)

    organization = models.OneToOneField(
        BluebottleOrganization,
        null=True,
        on_delete=models.CASCADE,
        related_name='activity_pub_organization'
    )

    objects = OrganizationManager()

    class Meta:
        verbose_name = _("partner")
        verbose_name_plural = _("partners")

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


class Event(ActivityPubModel):
    name = models.CharField(verbose_name=_('Activity title'))
    summary = models.TextField()
    image = models.ForeignKey(Image, null=True, on_delete=models.SET_NULL)
    activity = models.OneToOneField(
        "activities.Activity", null=True, on_delete=models.SET_NULL
    )
    url = models.URLField(null=True, blank=True)

    organization = models.ForeignKey(
        Organization, null=True, on_delete=models.SET_NULL
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

    @property
    def linked_activity(self):
        return self.linked_activities.first()

    @property
    def linked(self):
        return self.linked_activity is not None

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
        verbose_name = _("Shared activity")
        verbose_name_plural = _("Shated activities")


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


class JoinModeChoices(DjangoChoices):
    open = ChoiceItem('OpenJoinMode')
    review = ChoiceItem('ReviewJoinMode')


class AdoptionModeChoices(DjangoChoices):
    manual = ChoiceItem(
        'manual',
        _('Received activities are adopted manually.')
    )
    automatic = ChoiceItem(
        'automatic',
        _('Received activities are always automatically adopted and published.')
    )


class AdoptionTypeChoices(DjangoChoices):
    template = ChoiceItem(
        'template',
        _('Use received activities as template to create your own activities.')
    )
    link = ChoiceItem(
        'link',
        _('Show adopted activities as links to the partner platform.')
    )
    hosted = ChoiceItem(
        'hosted',
        _('Activities are managed by the partner platform, sign ups are synced.')
    )


class PublishModeChoices(DjangoChoices):
    manual = ChoiceItem(
        'manual',
        _('Activities will be shared manually.')
    )
    automatic = ChoiceItem(
        'automatic',
        _('Activities are automatically shared once they go live.')
    )


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
        related_name='sub_event'
    )
    slot = models.ForeignKey('time_based.DateActivitySlot', null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Sub event")
        verbose_name_plural = _("Sub events")


class DoGoodEvent(Event):
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    registration_deadline = models.DateTimeField(null=True)

    location = models.ForeignKey(Place, null=True, blank=True, on_delete=models.CASCADE)
    duration = models.DurationField(null=True)
    event_attendance_mode = models.CharField(
        choices=EventAttendanceModeChoices.choices,
        null=True
    )
    join_mode = models.CharField(
        choices=JoinModeChoices.choices,
        null=True
    )

    class Meta(Event.Meta):
        verbose_name = _('Date activity')
        verbose_name_plural = _('Date activities')


class Activity(ActivityPubModel):
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='activities')

    default_recipients = []

    def save(self, *args, **kwargs):
        from bluebottle.activity_pub.utils import get_platform_actor
        if not getattr(self, 'actor_id', None):
            self.actor = get_platform_actor()

        created = not self.pk

        super().save(*args, **kwargs)

        if created:
            for recipient in self.default_recipients:
                Recipient.objects.create(
                    actor=recipient,
                    activity=self
                )


class Recipient(models.Model):
    activity = models.ForeignKey('activity_pub.Activity', on_delete=models.CASCADE, related_name='recipients')
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='activities')
    send = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Recipient")
        verbose_name_plural = _("Recipients")
        unique_together = ('activity', 'actor')


class Follow(Activity):
    object = models.ForeignKey(
        'activity_pub.Actor',
        verbose_name=_("Partner"),
        on_delete=models.CASCADE
    )

    default_owner = models.ForeignKey(
        "members.Member",
        null=True,
        blank=True,
        verbose_name=_("Default activity owner"),
        help_text=_("This person will be the activity manager of the activities that are adopted."),
        on_delete=models.SET_NULL,
    )

    adoption_mode = models.CharField(
        choices=AdoptionModeChoices.choices,
        default=AdoptionModeChoices.manual,
        verbose_name=_("Adoption mode"),
        help_text=_("Select what should happen when a new activity has been received."),
    )

    adoption_type = models.CharField(
        choices=AdoptionTypeChoices.choices,
        default=AdoptionTypeChoices.template,
        verbose_name=_("Adoption type"),
        help_text=_("Select how a received activity should be adopted."),
    )

    publish_mode = models.CharField(
        choices=PublishModeChoices.choices,
        default=PublishModeChoices.manual,
        verbose_name=_("Publish mode"),
        help_text=_("Select how you want to share activities."),
    )

    @property
    def default_recipients(self):
        return [self.object]

    @property
    def shared_activities(self):
        if self.is_local:
            return Event.objects.filter(
                publish__actor=self.object,
            ).count()
        return Recipient.objects.filter(
            actor=self.actor,
            activity__publish__isnull=False,
            send=True
        ).count()

    @property
    def adopted_activities(self):
        return Announce.objects.filter(actor=self.actor).count()

    def __str__(self):
        return str(self.object)

    class Meta:
        verbose_name = _('Connection')
        verbose_name_plural = _('Connections')


class Follower(Follow):
    class Meta:
        proxy = True
        verbose_name = _('Consumer')
        verbose_name_plural = _('Consumers')


class Following(Follow):
    class Meta:
        proxy = True
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')

    def __str__(self):
        try:
            return str(self.object)
        except Actor.DoesNotExist:
            return "-"


class Accept(Activity):
    object = models.ForeignKey('activity_pub.Follow', on_delete=models.CASCADE)

    @property
    def default_recipients(self):
        return [self.object.actor]


class Publish(Activity):
    object = models.ForeignKey('activity_pub.Event', on_delete=models.CASCADE)


class Update(Activity):
    object = models.ForeignKey('activity_pub.Event', on_delete=models.CASCADE)

    @property
    def default_recipients(self):
        for publish in self.object.publish_set.all():
            for recipient in publish.recipients.all():
                yield recipient.actor


class Announce(Activity):
    object = models.ForeignKey('activity_pub.Event', on_delete=models.CASCADE)

    @property
    def default_recipients(self):
        publish = self.object.publish_set.first()
        return [publish.actor]


from .tasks import *  # noqa
