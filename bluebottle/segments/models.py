from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField

import wcag_contrast_ratio as contrast
from PIL import ImageColor

from colorfield.fields import ColorField
from future.utils import python_2_unicode_compatible

from bluebottle.utils.fields import ImageField
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection
from bluebottle.utils.utils import get_current_host, get_current_language, clean_html


@python_2_unicode_compatible
class SegmentType(models.Model):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)

    is_active = models.BooleanField(
        _('Is active'),
        default=True
    )
    user_editable = models.BooleanField(
        _('Editable in user profile'),
        default=True
    )
    enable_search = models.BooleanField(
        _('Enable search filters.'),
        default=False
    )

    @property
    def field_name(self):
        return 'segment__' + self.slug.replace('-', '_')

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(SegmentType, self).save(**kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)

    class JSONAPIMeta(object):
        resource_name = 'segment-types'


@python_2_unicode_compatible
class Segment(models.Model):
    name = models.CharField(_('name'), max_length=255)
    slug = models.CharField(_('slug'), max_length=255)

    alternate_names = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True
    )
    segment_type = models.ForeignKey(
        SegmentType,
        verbose_name=_('type'),
        related_name='segments',
        on_delete=models.CASCADE
    )

    email_domain = models.CharField(
        _('Email domain'), blank=True, null=True,
        max_length=255,
        help_text=_('Users with email addresses for this domain are automatically added to this segment')
    )

    tag_line = models.CharField(
        _('Slogan'), max_length=255, null=True, blank=True,
        help_text=_(
            'A short sentence to explain your segment. This sentence is directly visible on the page.'
        )
    )

    story = models.TextField(
        _('Story'), blank=True, null=True,
        help_text=_(
            'A more detailed story for your segment. This story can be accessed via a link on the page.'
        )
    )

    logo = ImageField(
        _("logo"), max_length=255, blank=True, null=True,
        upload_to='categories/logos/',
        help_text=_("The uploaded image will be scaled so that it is fully visible."),

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    background_color = ColorField(
        _('Background color'), null=True, blank=True,
        help_text=_(
            'Add a background colour to your segment page.'
        )
    )

    cover_image = ImageField(
        _("cover image"), max_length=255, blank=True, null=True,
        upload_to='categories/logos/',
        help_text=_("The uploaded image will be cropped to fit a 4:3 rectangle."),

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    def save(self, *args, **kwargs):
        if self.name not in self.alternate_names:
            self.alternate_names.append(self.name)

        if not self.slug:
            self.slug = slugify(self.name)

        if self.story:
            self.story = clean_html(self.story)

        super().save(*args, **kwargs)

    @property
    def text_color(self):
        rgb_background_color = [c / 256.0 for c in ImageColor.getcolor(self.background_color, 'RGB')]
        white = (1, 1, 1)

        contrast_with_white = contrast.rgb(rgb_background_color, white)

        if contrast.passes_AA(contrast_with_white, large=True):
            return 'white'
        else:
            return 'grey'

    def __str__(self):
        return u'{}: {}'.format(self.segment_type.name, self.name)

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        return u"{}/{}/initiatives/segments/details/{}/{}/".format(
            domain, language,
            self.pk,
            self.slug
        )

    class Meta:
        ordering = ('name',)
        unique_together = (('slug', 'segment_type'), )

    class JSONAPIMeta(object):
        resource_name = 'segments'
