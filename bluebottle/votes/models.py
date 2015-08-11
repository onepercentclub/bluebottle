from django.db import models
from django.conf import settings

from django.utils.translation import ugettext as _
from django_extensions.db.fields import CreationDateTimeField


class Vote(models.Model):
    """
    Mixin for generating an invoice reference.
    """
    created = CreationDateTimeField(_('created'))
    project = models.ForeignKey(settings.PROJECTS_PROJECT_MODEL)
    voter = models.ForeignKey(settings.AUTH_USER_MODEL,
                              verbose_name=_('voter'), blank=True, null=True)

    class Meta:
        unique_together = (('project', 'voter'), )
