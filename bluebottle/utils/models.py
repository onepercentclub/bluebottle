from builtins import object
from datetime import timedelta
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from djchoices.choices import DjangoChoices, ChoiceItem
from operator import attrgetter

from future.utils import python_2_unicode_compatible
from parler.models import TranslatableModel, TranslatedFields

import bluebottle.utils.monkey_patch_corsheaders  # noqa
import bluebottle.utils.monkey_patch_django_elasticsearch_dsl  # noqa
import bluebottle.utils.monkey_patch_migration  # noqa
import bluebottle.utils.monkey_patch_money_readonly_fields  # noqa
import bluebottle.utils.monkey_patch_parler  # noqa
import bluebottle.utils.monkey_patch_password_validators  # noqa
import bluebottle.utils.monkey_patch_jet  # noqa
from bluebottle.utils.managers import (
    SortableTranslatableManager,
    PublishedManager
)


@python_2_unicode_compatible
class Language(models.Model):
    """
    A language - ISO 639-1
    """
    code = models.CharField(max_length=2, blank=False)
    language_name = models.CharField(max_length=100, blank=False)
    native_name = models.CharField(max_length=100, blank=False)

    class Meta(object):
        ordering = ['language_name']

    def __str__(self):
        return self.language_name


@python_2_unicode_compatible
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

    class Meta(object):
        abstract = True

    def __str__(self):
        return self.line1[:80]


class MailLog(models.Model):

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    type = models.CharField(max_length=200)

    created = models.DateTimeField(auto_now_add=True)


@python_2_unicode_compatible
class BasePlatformSettings(models.Model):

    update = models.DateTimeField(auto_now=True)

    class Meta(object):
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

    def __str__(self):
        return str(_('Settings'))


class SortableTranslatableModel(TranslatableModel):
    class Meta(object):
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
        default=now,
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

    class Meta(object):
        abstract = True


class ValidatorError(Exception):
    def __init__(self, field, code, message):
        self.field = field
        self.code = code
        self.message = message
        super(ValidatorError, self).__init__(message)


class Validator(object):
    def __init__(self, instance):
        self.instance = instance

    def __call__(self):
        if not self.is_valid():
            raise ValidatorError(
                self.field, self.field, self.message
            )


class ValidatedModelMixin(object):
    validators = []
    required_fields = []

    @property
    def errors(self):
        for validator in self.validators:
            try:
                validator(self)()
            except ValidatorError as e:
                yield e

    @property
    def required(self):
        for field in self.required_fields:
            try:
                value = attrgetter(field)(self)
                if value in (None, ''):
                    yield field
            except ObjectDoesNotExist:
                yield field


class AnonymizationMixin(object):

    @property
    def anonymized(self):
        from bluebottle.members.models import MemberPlatformSettings
        anonymization_age = MemberPlatformSettings.load().anonymization_age
        if anonymization_age:
            return self.created < (now() - timedelta(days=anonymization_age))


class TranslationPlatformSettings(TranslatableModel, BasePlatformSettings):
    translations = TranslatedFields(
        office=models.CharField(
            'Office',
            max_length=100, null=True, blank=True
        ),

        office_location=models.CharField(
            'Office location',
            max_length=100, null=True, blank=True
        ),
        select_an_office_location=models.CharField(
            'Select an office location',
            max_length=100, null=True, blank=True
        ),
        whats_the_location_of_your_office=models.CharField(
            u'What\u2019s the location of your office?',
            max_length=100, null=True, blank=True
        ),

    )

    class Meta(object):
        verbose_name_plural = _('translation settings')
        verbose_name = _('translation settings')
