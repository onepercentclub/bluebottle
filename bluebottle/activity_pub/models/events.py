from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.utils.models import ChoiceItem, DjangoChoices

from bluebottle.activity_pub.models.base import ActivityPubModel, Image
from bluebottle.activity_pub.models.actors import Organization

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.utils import get_platform_actor


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
    video_url = models.URLField(
        _("video"),
        max_length=2048,
        blank=True,
        null=True,
        default="",
        help_text=_(
            "Make your activity come alive with a video. "
            "You can paste the link to YouTube or Vimeo here."
        ),
    )

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
        from bluebottle.activity_pub.models.activities import Create
        super().save(*args, **kwargs)

        if self.is_local:
            actor = get_platform_actor()
            if actor and not self.create_set.exists():
                Create.objects.create(actor=actor, object=self)

    @property
    def source(self):
        from bluebottle.activity_pub.models.activities import Create

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
    team = models.ForeignKey(
        'activity_pub.Team',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sub_events',
        help_text=_('Team this schedule slot belongs to (team-mode activities).'),
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
    participation_mode = models.CharField(
        choices=ParticipationModeChoices.choices,
        default=ParticipationModeChoices.individuals,
        null=True,
        blank=True,
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

    @property
    def is_team_activity(self):
        return self.participation_mode == ParticipationModeChoices.teams

    class Meta(Event.Meta):
        verbose_name = _('Date activity')
        verbose_name_plural = _('Date activities')
