from adminsortable.models import SortableMixin
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from parler.models import TranslatableModel, TranslatedFields

from bluebottle.fsm.triggers import TriggerMixin
from bluebottle.utils.fields import ImageField
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


class Poll(TriggerMixin, TranslatableModel):
    translations = TranslatedFields(
        title=models.CharField(_('title'), max_length=255),
        subtitle=models.CharField(
            _('subtitle'), max_length=255, blank=True, default=''
        ),
    )

    end_date = models.DateField(_('end date'), null=True, blank=True)
    status = models.CharField(max_length=40)

    class Meta:
        verbose_name = _('poll')
        verbose_name_plural = _('polls')
        ordering = ('-id',)
        permissions = (
            ('api_read_poll', 'Can view polls through the API'),
        )

    class JSONAPIMeta:
        resource_name = 'polls'

    def __str__(self):
        title = self.safe_translation_getter(
            'title',
            language_code=self.get_current_language() or settings.LANGUAGE_CODE,
            any_language=True,
        )
        return title or _('Poll {pk}').format(pk=self.pk)


class PollOption(SortableMixin, TranslatableModel):
    poll = models.ForeignKey(
        Poll,
        related_name='options',
        on_delete=models.CASCADE,
        verbose_name=_('poll'),
    )

    translations = TranslatedFields(
        title=models.CharField(_('title'), max_length=255),
        description=QuillField(_('description'), blank=True),
    )

    image = ImageField(
        _('image'),
        max_length=255,
        blank=True,
        null=True,
        upload_to='polls/options/',
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection,
        ],
    )
    video_url = models.URLField(
        _('video URL'),
        max_length=255,
        blank=True,
        null=True,
    )

    sequence = models.PositiveIntegerField(
        default=0, editable=False, db_index=True
    )

    class Meta:
        verbose_name = _('poll option')
        verbose_name_plural = _('poll options')
        ordering = ['sequence']

    class JSONAPIMeta:
        resource_name = 'polls/options'

    def __str__(self):
        title = self.safe_translation_getter(
            'title',
            language_code=self.get_current_language() or settings.LANGUAGE_CODE,
            any_language=True,
        )
        return title or _('Option {pk}').format(pk=self.pk)
