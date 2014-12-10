from django.db import models
from django.conf import settings
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from django.utils.translation import ugettext_lazy as _


class Terms(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL)

    creation_date = CreationDateTimeField(_('creation date'))
    modification_date = ModificationDateTimeField(_('last modification'))

    date = models.DateTimeField()

    contents = models.CharField(max_length=500000)
    version = models.CharField(max_length=40)

    def __unicode__(self):
        return 'Terms {0} - {1}'.format(self.version, self.date.date())

    class Meta:
        verbose_name_plural = 'Terms'


class TermsAgreement(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    terms = models.ForeignKey(Terms)
    creation_date = CreationDateTimeField(_('Date'))
