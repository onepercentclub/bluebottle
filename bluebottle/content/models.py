import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem

from django.conf import settings

from bluebottle.utils.fields import ImageField
from bluebottle.utils.models import PublishableModel, get_language_choices
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection
from bluebottle.utils.utils import get_current_host


YOUTUBE_PATTERN = re.compile(
    r'(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})'
)
VIMEO_PATTERN = re.compile(
    r'vimeo\.com/(?:video/)?(\d+)'
)


class ContentPage(PublishableModel):
    title = models.CharField(_('Title'), max_length=200)
    slug = models.SlugField(_('Slug'), unique=False)
    language = models.CharField(
        _('language'),
        max_length=7,
        choices=lazy(get_language_choices, list)()
    )
    full_page = models.BooleanField(
        _('Page without sub-navigation'),
        default=False,
    )
    show_title = models.BooleanField(
        default=True,
    )

    class Meta(object):
        ordering = ('language', 'slug')
        unique_together = ('language', 'slug')
        verbose_name = _('Content page')
        verbose_name_plural = _('Content pages')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f'/{self.language}/pages/{self.slug}'

    def get_admin_url(self):
        return get_current_host() + reverse(
            'admin:content_contentpage_change',
            args=[self.pk]
        )


class ContentBlock(models.Model):
    class BlockType(DjangoChoices):
        title = ChoiceItem('title', _('Title'))
        text = ChoiceItem('text', _('Text'))
        image = ChoiceItem('image', _('Image'))
        text_image = ChoiceItem('text_image', _('Text + image'))
        video = ChoiceItem('video', _('Video'))
        button = ChoiceItem('button', _('Button'))
        spacer = ChoiceItem('spacer', _('Spacer'))

    class ImageAlign(DjangoChoices):
        left = ChoiceItem('left', _('Left'))
        center = ChoiceItem('center', _('Center'))
        right = ChoiceItem('right', _('Right'))

    class TextImageAlign(DjangoChoices):
        left = ChoiceItem('left', _('Left'))
        right = ChoiceItem('right', _('Right'))

    class SpacerSize(DjangoChoices):
        small = ChoiceItem('small', _('Small'))
        medium = ChoiceItem('medium', _('Medium'))
        large = ChoiceItem('large', _('Large'))

    page = models.ForeignKey(
        ContentPage,
        related_name='blocks',
        on_delete=models.CASCADE,
    )
    block_type = models.CharField(
        max_length=20,
        choices=BlockType.choices,
    )
    sort_order = models.PositiveIntegerField(default=1)

    title_text = models.CharField(max_length=500, blank=True, default='')
    title_level = models.PositiveSmallIntegerField(default=1)

    text = models.TextField(blank=True, default='')

    image = ImageField(
        _('Image'),
        upload_to='content',
        blank=True,
        null=True,
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ],
    )
    align = models.CharField(
        max_length=10,
        choices=ImageAlign.choices,
        default=ImageAlign.center,
        blank=True,
    )
    ratio = models.PositiveSmallIntegerField(default=6, blank=True, null=True)

    video_url = models.URLField(blank=True, default='')
    video_provider = models.CharField(max_length=20, blank=True, default='')

    button_label = models.CharField(max_length=200, blank=True, default='')
    button_url = models.URLField(blank=True, default='')

    spacer_size = models.CharField(
        max_length=10,
        choices=SpacerSize.choices,
        default=SpacerSize.medium,
        blank=True,
    )

    class Meta(object):
        ordering = ('sort_order', 'pk')
        verbose_name = _('Content block')
        verbose_name_plural = _('Content blocks')

    def __str__(self):
        return f'{self.block_type} ({self.pk})'

    def clean(self):
        super().clean()
        if self.block_type == self.BlockType.video and self.video_url:
            provider = self.get_video_provider(self.video_url)
            if not provider:
                raise ValidationError({
                    'video_url': _('Only YouTube and Vimeo URLs are supported.')
                })

    def save(self, *args, **kwargs):
        if self.block_type == self.BlockType.video and self.video_url:
            self.video_provider = self.get_video_provider(self.video_url) or ''
        super().save(*args, **kwargs)

    @staticmethod
    def get_video_provider(url):
        if YOUTUBE_PATTERN.search(url):
            return 'youtube'
        if VIMEO_PATTERN.search(url):
            return 'vimeo'
        return None
