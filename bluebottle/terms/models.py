from builtins import object
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible


@python_2_unicode_compatible
class Terms(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)

    date = models.DateTimeField()

    contents = models.CharField(max_length=500000)
    version = models.CharField(max_length=40)

    def __str__(self):
        return 'Terms {0} - {1}'.format(self.version, self.date.date())

    class Meta(object):
        ordering = ('-date',)
        verbose_name_plural = _('Terms')
        verbose_name = _('Term')
        permissions = (
            ('api_read_terms', 'Can view terms through API'),
        )

    @classmethod
    def get_current(cls):
        queryset = cls.objects.filter(date__lte=now()).order_by('-date')
        if queryset.count():
            return queryset.all()[0]
        return None


class TermsAgreement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    terms = models.ForeignKey(Terms, on_delete=models.CASCADE)
    created = models.DateTimeField(_('Date'), auto_now_add=True)

    @classmethod
    def get_current(cls, user):
        terms = Terms.get_current()
        if terms:
            queryset = cls.objects.filter(user=user, terms=terms)
            if queryset.count():
                return queryset.all()[0]
        return None

    class Meta(object):
        ordering = ('-created',)
        verbose_name_plural = _('Terms agreement')
        verbose_name = _('Term agreements')
        permissions = (
            ('api_read_termsagreement', 'Can view terms agreements through API'),
        )
