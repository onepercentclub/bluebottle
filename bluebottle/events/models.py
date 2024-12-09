from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.triggers import TriggerMixin

EVENT_TYPES = (
    ('donation.succeeded', _('Donation done')),
    ('funding.approved', _('Funding campaign published')),
    ('funding.succeeded', _('Funding campaign succeeded')),
    ('funding.50%', _('Funding campaign at 50%')),
    ('funding.100%', _('Funding campaign at 100%')),
)


class Event(TriggerMixin, models.Model):
    limit = models.Q(app_label='funding', model='donation') | models.Q(app_label='funding', model='funding')
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
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
