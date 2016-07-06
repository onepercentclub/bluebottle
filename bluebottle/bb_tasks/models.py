from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from djchoices.choices import DjangoChoices, ChoiceItem


class BaseSkill(models.Model):
    name = models.CharField(_('english name'), max_length=100, unique=True)
    name_nl = models.CharField(_('dutch name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        abstract = True
