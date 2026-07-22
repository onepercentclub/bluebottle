from urllib.parse import urlparse

from django.contrib.contenttypes.fields import GenericForeignKey
import inflection

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from django.contrib.contenttypes.models import ContentType
from django.db import models, connection
from django.urls import reverse, resolve
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField
from polymorphic.models import PolymorphicManager, PolymorphicModel

from bluebottle.activities.models import Activity as DoGoodActivity, RemoteMember
from bluebottle.time_based.models import Registration
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import Member
from bluebottle.organizations.models import Organization as BluebottleOrganization
from bluebottle.files.models import Image as BluebottleImage
from bluebottle.utils.models import ChoiceItem, DjangoChoices

from bluebottle.activity_pub.tasks import publish_to_recipient
from bluebottle.activity_pub.utils import is_local, get_platform_actor

from bluebottle.activity_pub.adapters import adapter


class ActivityPubManager(PolymorphicManager):
    def get_queryset(self):
        qs = self.queryset_class(self.model, using=self._db, hints=self._hints)
        return qs

    def from_iri(self, iri):
        if iri:
            if is_local(iri):
                resolved = resolve(urlparse(iri).path)
                return self.filter(pk=resolved.kwargs['pk']).first()
            else:
                return self.filter(iri=iri).first()


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
            model_name = self.__class__.__name__
            return connection.tenant.build_absolute_url(
                reverse(
                    'json-ld:resource',
                    args=(
                        inflection.dasherize(inflection.underscore(model_name)),
                        str(self.pk),
                    )
                )
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
        return Follow.objects.filter(object=self).first()

    @property
    def webfinger_uri(self):
        if self.preferred_username:
            return f'acct:{self.preferred_username}@{connection.tenant.domain_url}'

    def save(self, *args, **kwargs):
        if self.is_local:
            if not self.inbox:
                self.inbox = Inbox.objects.create()
            if not self.outbox:
                self.outbox = Outbox.objects.create()
            if not self.public_key:
                self.public_key = PublicKey.objects.create()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_real_instance().name


class Person(Actor):
    name = models.TextField()
    given_name = models.TextField(null=True, blank=True)
    family_name = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)

    origin = models.OneToOneField(
        Member,
        null=True,
        on_delete=models.CASCADE,
        related_name='activity_pub_model'
    )

    adopted = models.OneToOneField(
        RemoteMember,
        null=True,
        on_delete=models.CASCADE,
        related_name='origin'
    )

    source = models.ForeignKey(
        'activity_pub.Organization', null=True, on_delete=models.SET_NULL
    )

    @property
    def follow(self):
        follow = Follow.objects.filter(object=self).first()
        return follow

    def __str__(self):
        return self.name


class Image(ActivityPubModel):
    name = models.CharField(max_length=1000, null=True)
    url = models.URLField(null=True)

    origin = models.OneToOneField(
        BluebottleImage,
        null=True,
        on_delete=models.CASCADE,
        related_name='activity_pub_model'
    )

    adopted = models.OneToOneField(
        BluebottleImage,
        null=True,
        on_delete=models.CASCADE,
        related_name='origin'
    )


class Organization(Actor):
    name = models.CharField(max_length=300)
    summary = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)

    image = models.ForeignKey(Image, null=True, on_delete=models.SET_NULL)
    icon = models.ForeignKey(Image, null=True, on_delete=models.SET_NULL)

    origin = models.OneToOneField(
        BluebottleOrganization,
        null=True,
        on_delete=models.CASCADE,
        related_name='activity_pub_model'
    )

    adopted = models.OneToOneField(
        BluebottleOrganization,
        null=True,
        on_delete=models.CASCADE,
        related_name='origin'
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.is_local and not self.adopted:
            adapter.adopt(self)

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
    summary = models.TextField(null=True, blank=True)

    street_address = models.CharField(max_length=1000, null=True)
    postal_code = models.CharField(max_length=1000, null=True)

    locality = models.CharField(max_length=1000, null=True)
    region = models.CharField(max_length=1000, null=True)
    country = models.CharField(max_length=1000, null=True)


class Place(ActivityPubModel):
    name = models.CharField(max_length=1000)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.SET_NULL)

    origin = models.OneToOneField(
        "geo.Geolocation", null=True, on_delete=models.SET_NULL, related_name='activity_pub_model'
    )
    adopted = models.OneToOneField(
        "geo.Geolocation", null=True, on_delete=models.SET_NULL, related_name='origin'
    )

    def __str__(self):
        return self.name or self.id


class Event(ActivityPubModel):
    name = models.CharField(verbose_name=_('Activity title'))
    summary = models.TextField(blank=True, null=True)
    image = models.ForeignKey(Image, null=True, on_delete=models.SET_NULL)
    origin = models.OneToOneField(
        "activities.Activity", null=True, on_delete=models.SET_NULL, related_name='activity_pub_model'
    )
    adopted = models.OneToOneField(
        "activities.Activity", null=True, on_delete=models.SET_NULL, related_name='origin'
    )

    link = models.OneToOneField(
        "activity_links.LinkedActivity",
        null=True,
        on_delete=models.SET_NULL,
        related_name='origin'
    )

    url = models.URLField(null=True, blank=True)

    organization = models.ForeignKey(
        Organization, null=True, on_delete=models.SET_NULL
    )
    contributor_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Total contributors from all platforms')
    )

    @classmethod
    def sync(cls, activity):
        return adapter.sync(activity)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.is_local:
            if not self.create_set.exists():
                Create.objects.create(actor=get_platform_actor(), object=self)

    @property
    def source(self):
        create = Create.objects.filter(object=self).first()
        if create:
            return create.actor

    @property
    def adopted_activity(self):
        return self.adopted or self.link

    @property
    def adoption_type(self):
        return self.create_set.get().actor.follow.short_adoption_type

    @property
    def title(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Shared/Received activity")
        verbose_name_plural = _("Shared/Received activities")


class PublishedActivity(Event):

    class Meta:
        proxy = True
        verbose_name = _("Shared activity")
        verbose_name_plural = _("Shared activities")


class ReceivedActivity(Event):

    class Meta:
        proxy = True
        verbose_name = _("Received activity")
        verbose_name_plural = _("Received activities")


class GoodDeed(Event):
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    activity_type = 'deed'

    class Meta:
        verbose_name = _("Deed")
        verbose_name_plural = _("Deeds")


class CollectCampaign(Event):
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    location = models.ForeignKey(Place, null=True, blank=True, on_delete=models.SET_NULL)
    target = models.FloatField(null=True)
    donated = models.FloatField(null=True)
    collect_type = models.CharField(
        verbose_name=_("Type"),
        max_length=200,
        null=True,
    )

    activity_type = 'collectactivity'

    class Meta:
        verbose_name = _("Collect campaign")
        verbose_name_plural = _("Collect campaigns")


class CrowdFunding(Event):
    target = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    target_currency = models.CharField(max_length=3, default='EUR')
    donated = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    donated_currency = models.CharField(max_length=3, default='EUR')

    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    location = models.ForeignKey(Place, null=True, blank=True, on_delete=models.SET_NULL)

    activity_type = 'funding'

    class Meta:
        verbose_name = _("Funding")
        verbose_name_plural = _("Funding")


class GrantApplication(Event):
    target = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    target_currency = models.CharField(max_length=3, null=True, blank=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    location = models.ForeignKey(Place, null=True, blank=True, on_delete=models.CASCADE)

    activity_type = 'grantapplication'

    class Meta:
        verbose_name = _("Grant application")
        verbose_name_plural = _("Grant applications")


class EventAttendanceModeChoices(DjangoChoices):
    online = ChoiceItem('OnlineEventAttendanceMode')
    offline = ChoiceItem('OfflineEventAttendanceMode')


class JoinModeChoices(DjangoChoices):
    open = ChoiceItem('OpenJoinMode')
    review = ChoiceItem('ReviewJoinMode')
    selected = ChoiceItem('SelectedJoinMode')


class SlotModeChoices(DjangoChoices):
    set = ChoiceItem('SetSlotMode')
    scheduled = ChoiceItem('ScheduledSlotMode')
    periodic = ChoiceItem('PeriodicSlotMode')


class RepetitionModeChoices(DjangoChoices):
    daily = ChoiceItem('DailyRepetitionMode')
    weekly = ChoiceItem('WeeklyRepetitionMode')
    monthly = ChoiceItem('MonthlyRepetitionMode')


class ParticipationModeChoices(DjangoChoices):
    individuals = ChoiceItem('IndividualParticipationMode')
    teams = ChoiceItem('TeamParticipationMode')
    any = ChoiceItem('AnyParticipationMode')


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
    clone = ChoiceItem(
        'clone',
        _('Use received activities as template to create your own activities.')
    )
    link = ChoiceItem(
        'link',
        _('Show adopted activities as links to the partner platform.')
    )
    sync = ChoiceItem(
        'sync',
        _('Fully synced copy; Participants sync with source.')
    )


class ShortAdoptionTypeChoices(DjangoChoices):
    clone = ChoiceItem(
        'clone',
        _('Template')
    )
    link = ChoiceItem(
        'link',
        _('Link')
    )
    sync = ChoiceItem(
        'sync',
        _('Fully synced')
    )


class PublishModeChoices(DjangoChoices):
    manual = ChoiceItem(
        'manual',
        _('Choose which activities you want to share')
    )
    automatic = ChoiceItem(
        'automatic',
        _('Activities will be shared when they go live.')
    )


class SubEvent(ActivityPubModel):
    name = models.CharField(null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    location = models.ForeignKey(Place, null=True, blank=True, on_delete=models.SET_NULL)
    duration = models.DurationField(null=True)
    event_attendance_mode = models.CharField(
        choices=EventAttendanceModeChoices.choices,
        null=True,
        blank=True,
    )
    parent = models.ForeignKey(
        'activity_pub.DoGoodEvent',
        null=True,
        on_delete=models.CASCADE,
        related_name='sub_event'
    )
    contributor_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Accepted participants for this slot.'),
    )
    capacity = models.PositiveIntegerField(
        _('Capacity'),
        null=True,
        blank=True,
        help_text=_('Per-slot attendee limit (schema.org maximumAttendeeCapacity). Mirrors activity slot.'),
    )

    origin_content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE)
    origin_id = models.PositiveBigIntegerField(null=True)
    origin = GenericForeignKey("origin_content_type", "origin_id")

    adopted_content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE)
    adopted_id = models.PositiveBigIntegerField(null=True)
    adopted = GenericForeignKey("adopted_content_type", "adopted_id")

    @property
    def title(self):
        return self.name

    class Meta:
        verbose_name = _("Sub event")
        verbose_name_plural = _("Sub events")


class DoGoodEvent(Event):
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    application_deadline = models.DateTimeField(null=True)

    location = models.ForeignKey(Place, null=True, blank=True, on_delete=models.SET_NULL)
    duration = models.DurationField(null=True)
    repetition_mode = models.CharField(
        choices=RepetitionModeChoices.choices,
        null=True
    )
    event_attendance_mode = models.CharField(
        choices=EventAttendanceModeChoices.choices,
        null=True,
        blank=True,
    )
    join_mode = models.CharField(
        choices=JoinModeChoices.choices,
        null=True
    )

    slot_mode = models.CharField(
        choices=SlotModeChoices.choices,
        default=SlotModeChoices.set,
        null=True
    )
    capacity = models.PositiveIntegerField(
        _('maximum attendee capacity'),
        null=True,
        blank=True,
        help_text=_('Overall attendee limit (schema.org maximumAttendeeCapacity). Mirrors time-based activity.'),
    )

    @property
    def activity_type(self):
        if self.slot_mode == 'ScheduledSlotMode':
            return 'ScheduleActivity'
        elif self.slot_mode == 'PeriodicSlotMode':
            return 'PeriodicActivity'
        elif self.join_mode == 'SelectedJoinMode':
            return 'RegisteredDateActivity'
        elif len(self.sub_event.all()) > 0:
            return 'DateActivity'
        else:
            return 'DeadlineActivity'

    class Meta(Event.Meta):
        verbose_name = _('Date activity')
        verbose_name_plural = _('Date activities')


class Activity(ActivityPubModel):
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='activities')

    default_recipients = []

    def save(self, *args, **kwargs):
        if not getattr(self, 'actor_id', None):
            self.actor = get_platform_actor()

        created = not self.pk

        super().save(*args, **kwargs)

        if created and self.is_local:
            for recipient in self.default_recipients:
                Recipient.objects.create(
                    actor=recipient,
                    activity=self
                )


class Recipient(models.Model):
    activity = models.ForeignKey('activity_pub.Activity', on_delete=models.CASCADE, related_name='recipients')
    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='recipients')
    send = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)

        if created and not self.actor.is_local:
            publish_to_recipient.delay_on_commit(self, connection.tenant)

            if isinstance(self.activity, Create):
                for transition_cls in [Start, Finish, Cancel]:
                    for transition in transition_cls.objects.filter(
                        object=self.activity.object
                    ):
                        Recipient.objects.get_or_create(
                            actor=self.actor,
                            activity=transition
                        )

    def publish(self):
        adapter.publish(self.activity, self.actor)

        self.send = True
        self.save()

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
        help_text=_(
            "This user will be assigned as the activity manager for any activity "
            "cloned from a template. It can be left empty and no activity manager "
            "will be assigned by default."
        ),
        on_delete=models.SET_NULL,
    )

    automatic_adoption_activity_types = MultiSelectField(
        verbose_name=_("Automatically adopted these activity types"),
        max_length=300,
        choices=InitiativePlatformSettings.ACTIVITY_TYPES,
        null=True,
        blank=True,
        help_text=_("Selected activity types are automatically adopted when they are published."),
    )

    adoption_type = models.CharField(
        choices=AdoptionTypeChoices.choices,
        default=AdoptionTypeChoices.clone,
        verbose_name=_("Adoption type"),
        help_text=_("Select how a received activity should be adopted."),
    )

    publish_mode = models.CharField(
        choices=PublishModeChoices.choices,
        default=PublishModeChoices.manual,
        verbose_name=_("Publish mode"),
    )

    def follow(self, url, **kwargs):
        self.object = adapter.discover(url)

    @property
    def default_recipients(self):
        return [self.object]

    @property
    def shared_activities(self):
        if self.is_local:
            return Event.objects.filter(
                create__actor=self.object,
            )
        return Recipient.objects.filter(
            actor=self.actor,
            activity__create__isnull=False,
            send=True
        )

    @property
    def short_adoption_type(self):
        # `adoption_type` is stored on Follow and may contain legacy/unknown values.
        # The admin should never 500 because of an unexpected choice value.
        return ShortAdoptionTypeChoices.labels.get(
            self.adoption_type,
            str(self.adoption_type) if self.adoption_type is not None else ''
        )

    @property
    def adopted_activities(self):
        if self.is_local:
            return Event.objects.filter(
                create__actor=self.object,
            ).filter(
                models.Q(link__isnull=False) | models.Q(adopted__isnull=False)
            )
        return Accept.objects.filter(
            actor=self.actor,
        )

    @property
    def unpublished_activities(self):
        return DoGoodActivity.objects.filter(
            status__in=['open', 'succeeded', 'full', 'partially_funded', 'running'],
        ).exclude(
            activity_pub_model__create__recipients__actor=self.actor,
        )

    @property
    def unpublished_open_activities(self):
        return self.unpublished_activities.filter(
            status__in=['open', 'full', 'running'],
        )

    @property
    def unpublished_succeeded_activities(self):
        return self.unpublished_activities.filter(
            status__in=['succeeded', 'partially_funded'],
        )

    def save(self, *args, **kwargs):
        created = not bool(self.pk)

        if not hasattr(self, 'actor'):
            self.actor = get_platform_actor()

        super().save(*args, **kwargs)

        if not created:
            Update.objects.create(
                object=self
            )

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
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)

    @property
    def default_recipients(self):
        if isinstance(self.object, Follow):
            yield self.object.actor
        elif isinstance(self.object, Event):
            create = self.object.create_set.first()
            yield create.actor
        elif isinstance(self.object, Join) and self.object.platform:
            yield self.object.platform

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)

        if created and not self.is_local and isinstance(self.object, Join):
            registration = Registration.objects.get(
                user=self.object.actor.origin, activity=self.object.object.adopted
            )
            try:
                registration.states.accept(save=True)
            except TransitionNotPossible:
                pass


class Reject(Activity):
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)

    @property
    def default_recipients(self):
        yield self.object.platform

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)

        if created and not self.is_local and isinstance(self.object, Join):
            registration = Registration.objects.get(
                user=self.object.actor.origin, activity=self.object.object.adopted
            )
            registration.states.reject(save=True)


class Create(Activity):
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)

        if created and self.is_local:
            if self.object.origin:
                if isinstance(self.object, Event):
                    Start.objects.create(object=self.object)
                elif self.object.origin.status == 'succeeded':
                    Finish.objects.create(object=self.object)
                elif self.object.origin.status in ('cancelled', 'rejected', 'deleted', 'expired'):
                    Cancel.objects.create(object=self.object)
        elif not self.is_local:
            follow = Follow.objects.get(object=self.actor)

            if (
                (
                    isinstance(self.object, Event) and
                    self.object.activity_type.lower() in follow.automatic_adoption_activity_types
                ) or
                isinstance(self.object, SubEvent)
            ):
                if follow.adoption_type == 'sync':
                    adapter.adopt(self.object)
                elif follow.adoption_type == 'link':
                    adapter.link(self.object)

    @property
    def followers(self):
        actor = get_platform_actor()
        followers = Follow.objects.filter(publish_mode='automatic', accept__actor=actor)
        return followers

    @property
    def default_recipients(self):
        if isinstance(self.object, SubEvent):
            return [recipient.actor for recipient in self.object.parent.create_set.get().recipients.all()]
        else:
            return [follower.actor for follower in self.followers]


class Update(Activity):
    object = models.ForeignKey(ActivityPubModel, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if created and not self.object.is_local:
            if hasattr(self.object, 'adopted') and self.object.adopted:
                adapter.adopt(self.object)
            elif hasattr(self.object, 'link') and self.object.link:
                adapter.link(self.object)

    @property
    def default_recipients(self):
        if isinstance(self.object, Follow):
            yield self.object.object

        elif isinstance(self.object, Event):
            for create in self.object.create_set.all():
                for recipient in create.recipients.all():
                    yield recipient.actor
        elif isinstance(self.object, SubEvent):
            parent = self.object.parent
            if parent:
                for create in parent.create_set.all():
                    for recipient in create.recipients.all():
                        yield recipient.actor

        elif isinstance(self.object, Organization):
            for follow in self.object.activities.instance_of(Follow):
                yield follow.object
        elif isinstance(self.object, Person):
            recipients = set()
            for join in self.object.activities.all().instance_of(Join):
                for recipient in join.recipients.all():
                    recipients.add(recipient.actor)

            for recipient in recipients:
                yield recipient
        else:
            raise TypeError(f'Cannot create Update for {self.object}')


class Join(Activity):
    """Sent by a follower when a user joins an Event"""
    object = models.ForeignKey(ActivityPubModel, on_delete=models.CASCADE)
    motivation = models.TextField(null=True, blank=True)

    platform = models.ForeignKey(Organization, null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.is_local:
            adapter.adopt(self)

    @property
    def default_recipients(self):
        if not self.actor.is_local:
            yield self.actor
            return

        try:
            create = self.object.create_set.get()
        except (AttributeError, Create.DoesNotExist):
            create = self.object.parent.create_set.get()

        if not create.actor.is_local:
            yield create.actor


class Transition(Activity):
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)
    transitioned = models.BooleanField(default=False)

    @property
    def default_recipients(self):
        for create in self.object.create_set.all():
            for recipient in create.recipients.all():
                yield recipient.actor

    def save(self, *args, **kwargs):
        if not self.is_local and not self.transitioned:
            if self.transition():
                self.transitioned = True

        super().save(*args, **kwargs)

    def transition(self):
        raise NotImplementedError()


class Leave(Transition):
    """Sent by a follower when a user leaves a synced activity; object is the source Event."""
    @property
    def default_recipients(self):
        create = self.object.create_set.first()
        if create:
            yield create.actor

    def transition(self):
        if self.object.is_local:
            if isinstance(self.object, DoGoodEvent) and self.object.activity_type == 'PeriodicActivity':
                registration = self.object.origin.registrations.get(
                    remote_user=self.actor.adopted
                )
                registration.states.stop(save=True)
            else:
                contributor = self.object.origin.contributors.get(
                    remote_user=self.actor.adopted
                )
                contributor.states.withdraw(save=True)

            return True


class Delete(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.cancel(save=True)
            return True

        if self.object.link:
            self.object.link.delete()
            return True


class Start(Transition):
    def transition(self):
        if self.object.adopted:
            try:
                self.object.adopted.states.publish(save=True)
                return True
            except TransitionNotPossible:
                pass

        if self.object.link:
            try:
                self.object.link.states.start(save=True)
                return True
            except TransitionNotPossible:
                pass


class Cancel(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.cancel(save=True)
            return True

        if self.object.link:
            self.object.link.states.cancel(save=True)
            return True


class Finish(Transition):
    def transition(self):
        if self.object.adopted:
            try:
                self.object.adopted.states.succeed(save=True)
            except TransitionNotPossible:
                pass

            return True

        if self.object.link:
            self.object.link.states.succeed(save=True)
            return True


class Lock(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.lock(save=True)
            return True


from bluebottle.activity_pub.signals import *  # noqa
