from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.triggers import TriggerMixin

EVENT_TYPES = (
    ('deed-participant.succeeded', _('Participant succeeded')),
    ('deed.succeeded', _('Deed succeeded')),
    ('deed.published', _('Deed published')),
    ('donation.succeeded', _('Donation done')),
    ('funding.approved', _('Funding campaign published')),
    ('funding.succeeded', _('Funding campaign succeeded')),
    ('funding.25%', _('Funding campaign at 25%')),
    ('funding.50%', _('Funding campaign at 50%')),
    ('funding.75%', _('Funding campaign at 75%')),
    ('funding.100%', _('Funding campaign at 100%')),
)


class Event(TriggerMixin, models.Model):
    limit = (models.Q(app_label='funding')
             | models.Q(app_label='deeds')
             | models.Q(app_label='collect')
             | models.Q(app_label='time_based'))
    content_type = models.ForeignKey(ContentType, limit_choices_to=limit, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey(
        "content_type", "object_id"
    )
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=40)

    class Meta:
        ordering = ['-created']
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    class JSONAPIMeta():
        resource_name = 'events'


class Webhook(models.Model):
    url = models.URLField(max_length=256)

    class Meta:
        verbose_name = _('Event webhook')
        verbose_name_plural = _('Event webhooks')
