from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

import bluebottle.utils.monkey_patch_migration  # noqa
import bluebottle.utils.monkey_patch_corsheaders  # noqa
import bluebottle.utils.monkey_patch_parler  # noqa
import bluebottle.utils.monkey_patch_money_readonly_fields  # noqa


class Language(models.Model):
    """
    A language - ISO 639-1
    """
    code = models.CharField(max_length=2, blank=False)
    language_name = models.CharField(max_length=100, blank=False)
    native_name = models.CharField(max_length=100, blank=False)

    class Meta:
        ordering = ['language_name']

    def __unicode__(self):
        return self.language_name


class Address(models.Model):
    """
    A postal address.
    """
    line1 = models.CharField(max_length=100, blank=True)
    line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.ForeignKey('geo.Country', blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.line1[:80]


class MailLog(models.Model):

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    type = models.CharField(max_length=200)

    created = models.DateTimeField(auto_now_add=True)


class BasePlatformSettings(models.Model):

    update = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(BasePlatformSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()
