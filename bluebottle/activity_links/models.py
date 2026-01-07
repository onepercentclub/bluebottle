from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from djmoney.money import Money
from polymorphic.models import PolymorphicModel, PolymorphicManager

from bluebottle.organizations.models import Organization
from bluebottle.utils.fields import MoneyField, ImageField


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

        organization = Publish.objects.filter(object=event).first().actor.organization

        return serializer.save(
            event=event, host_organization=organization, status='open'
        )


class LinkedActivity(PolymorphicModel):
    title = models.CharField(max_length=255)
    link = models.URLField()
    status = models.CharField(max_length=40)
    description = QuillField(_("Description"), blank=True)
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

    def __str__(self):
        return self.title


class LinkedDeed(LinkedActivity):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)

    @property
    def succeeded_contributor_count(self):
        return 0

    @property
    def activity_date(self):
        return None

    class JSONAPIMeta(object):
        resource_name = 'activities/deeds'


class LinkedFunding(LinkedActivity):
    target = MoneyField()
    donated = MoneyField(default=Money('0.00', 'EUR'))
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)


class LinkedDeadlineActivity(LinkedActivity):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)


class LinkedDateActivity(LinkedActivity):
    pass


class LinkedDateSlot(models.Model):
    activity = models.ForeignKey(
        LinkedActivity,
        related_name='slots',
        on_delete=models.CASCADE,
    )
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)


@receiver(post_save, sender=LinkedDeed)
def es_upsert_linked_deed(sender, instance, **kwargs):
    from bluebottle.activity_links.documents import LinkedDeedDocument
    LinkedDeedDocument().update(instance, refresh="wait_for")


@receiver(post_delete, sender=LinkedDeed)
def es_delete_linked_deed(sender, instance, **kwargs):
    from bluebottle.activity_links.documents import LinkedDeedDocument
    LinkedDeedDocument().delete(instance, refresh="wait_for")


from bluebottle.activity_links.signals import *  # noqa
