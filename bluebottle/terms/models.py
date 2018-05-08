from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django_extensions.db.fields import CreationDateTimeField, \
    ModificationDateTimeField
from django.utils.translation import ugettext_lazy as _


class Terms(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL)

    created = CreationDateTimeField(_('creation date'))
    updated = ModificationDateTimeField(_('last modification'))

    date = models.DateTimeField()

    contents = models.CharField(max_length=500000)
    version = models.CharField(max_length=40)

    def __unicode__(self):
        return 'Terms {0} - {1}'.format(self.version, self.date.date())

    class Meta:
        ordering = ('-date',)
        verbose_name_plural = _('Terms')
        verbose_name = _('Term')

    @classmethod
    def get_current(cls):
        queryset = cls.objects.filter(date__lte=now()).order_by('-date')
        if queryset.count():
            return queryset.all()[0]
        return None


class TermsAgreement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    terms = models.ForeignKey(Terms)
    created = CreationDateTimeField(_('Date'))

    @classmethod
    def get_current(cls, user):
        terms = Terms.get_current()
        if terms:
            queryset = cls.objects.filter(user=user, terms=terms)
            if queryset.count():
                return queryset.all()[0]
        return None

    class Meta:
        ordering = ('-created',)
        verbose_name_plural = _('Terms agreement')
        verbose_name = _('Term agreements')
