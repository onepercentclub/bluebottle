from django.db import models
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from djmoney.money import Money
from polymorphic.models import PolymorphicModel, PolymorphicManager

from bluebottle.files.fields import ImageField
from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.organizations.models import Organization
from bluebottle.utils.fields import MoneyField


class LinkedActivityManager(PolymorphicManager):
    def sync(self, event):
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer
        from bluebottle.activity_links.serializers import LinkedActivitySerializer

        try:
            instance = self.get(event=event)
        except LinkedActivity.DoesNotExist:
            instance = None

        data = EventSerializer(instance=event).data
        serializer = LinkedActivitySerializer(
            data=data, instance=instance
        )
        serializer.is_valid(raise_exception=True)

        follow = Follow.objects.get(object=event.create_set.first().actor)

        activity_type = serializer.validated_data['type'].lower()
        if activity_type == 'collectcampaign':
            activity_type = 'collectactivity'

        if activity_type == 'gooddeed':
            activity_type = 'deed'

        if (
            activity_type in follow.automatic_adoption_activity_types or
            serializer.instance
        ):
            organization = Create.objects.filter(object=event).first().actor.organization

            return serializer.save(
                event=event, host_organization=organization
            )


class LinkedActivity(TriggerMixin, PolymorphicModel):
    title = models.CharField(max_length=255)
    link = models.URLField()
    status = models.CharField(max_length=40)
    description = QuillField(_("Description"), blank=True)

    archived = models.BooleanField(
        _('Archive'),
        help_text=_('Archive this link. It will no longer appear in search results.'),
        default=False
    )

    image = ImageField(blank=True, null=True)

    event = models.ForeignKey(
        'activity_pub.Event',
        related_name='linked_activities',
        null=True,
        on_delete=models.SET_NULL
    )
    host_organization = models.ForeignKey(
        Organization,
        related_name='linked_activities',
        null=True,
        on_delete=models.SET_NULL,
    )

    objects = LinkedActivityManager()

    class Meta:
        verbose_name_plural = _('Linked activities')
        verbose_name = _('linked activity')

    def __str__(self):
        return self.title


class LinkedDeed(LinkedActivity):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    activity_type = _('Deed')

    @property
    def succeeded_contributor_count(self):
        return 0

    @property
    def activity_date(self):
        return None

    class JSONAPIMeta(object):
        resource_name = 'activities/deeds'


class LinkedCollectCampaign(LinkedActivity):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    collect_type = models.CharField(max_length=1000, null=True, blank=True)
    location = models.ForeignKey('geo.Geolocation', null=True, blank=True, on_delete=models.SET_NULL)
    location_hint = models.CharField(max_length=1000, null=True, blank=True)
    activity_type = _('Collect campaign')

    class JSONAPIMeta(object):
        resource_name = 'activities/collects'


class LinkedFunding(LinkedActivity):
    target = MoneyField()
    donated = MoneyField(default=Money('0.00', 'EUR'))
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    location = models.ForeignKey('geo.Geolocation', null=True, blank=True, on_delete=models.SET_NULL)
    activity_type = _('Crowd-funding')


class LinkedGrantApplication(LinkedActivity):
    target = MoneyField(null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    location = models.ForeignKey('geo.Geolocation', null=True, blank=True, on_delete=models.SET_NULL)
    activity_type = _('Grant application')


class LinkedDeadlineActivity(LinkedActivity):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    location = models.ForeignKey('geo.Geolocation', null=True, blank=True, on_delete=models.SET_NULL)
    activity_type = _('Flexible activity')


class LinkedDateActivity(LinkedActivity):
    activity_type = _('Date activity')


class LinkedDateSlot(models.Model):
    activity = models.ForeignKey(
        LinkedActivity,
        related_name='slots',
        on_delete=models.CASCADE,
    )
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    location = models.ForeignKey('geo.Geolocation', null=True, blank=True, on_delete=models.SET_NULL)

    status = 'open'

    @property
    def duration(self):
        if self.start and self.end:
            return self.end - self.start
        return None


class LinkedPeriodicActivity(LinkedActivity):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    location = models.ForeignKey('geo.Geolocation', null=True, blank=True, on_delete=models.SET_NULL)
    period = models.CharField(null=True, blank=True, max_length=255)
    activity_type = _('Recurring activity')


class LinkedScheduleActivity(LinkedActivity):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    location = models.ForeignKey('geo.Geolocation', null=True, blank=True, on_delete=models.SET_NULL)
    activity_type = _('Past date activity')


from bluebottle.activity_links.signals import *  # noqa
