
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from djchoices.choices import DjangoChoices, ChoiceItem
from parler.models import TranslatableModel

from bluebottle.utils.managers import SortableTranslatableManager, PublishedManager

import bluebottle.utils.monkey_patch_migration  # noqa
import bluebottle.utils.monkey_patch_corsheaders  # noqa
import bluebottle.utils.monkey_patch_parler  # noqa
import bluebottle.utils.monkey_patch_money_readonly_fields  # noqa
import bluebottle.utils.monkey_patch_django_elasticsearch_dsl  # noqa


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

    def __unicode__(self):
        return 'Settings'


class SortableTranslatableModel(TranslatableModel):
    class Meta:
        abstract = True

    objects = SortableTranslatableManager()


class PublishedStatus(DjangoChoices):
    published = ChoiceItem('published', label=_("Published"))
    draft = ChoiceItem('draft', label=_("Draft"))


class PublishableModel(models.Model):

    # Publication
    status = models.CharField(_('status'), max_length=20,
                              choices=PublishedStatus.choices,
                              default=PublishedStatus.draft, db_index=True)
    publication_date = models.DateTimeField(
        _('publication date'),
        null=True, db_index=True,
        default=now(),
        help_text=_("To go live, status must be 'Published'."))

    publication_end_date = models.DateTimeField(_('publication end date'),
                                                null=True, blank=True,
                                                db_index=True)
    # Metadata
    author = models.ForeignKey('members.Member',
                               verbose_name=_('author'), blank=True, null=True)
    creation_date = CreationDateTimeField(_('creation date'))
    modification_date = ModificationDateTimeField(_('last modification'))

    objects = PublishedManager()

    class Meta:
        abstract = True
