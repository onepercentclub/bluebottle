from builtins import object
from django.conf import settings
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.functional import lazy
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem


from fluent_contents.extensions.model_fields import PluginHtmlField, PluginImageField
from fluent_contents.models import PlaceholderField
from fluent_contents.models.db import ContentItem
from fluent_contents.models.fields import ContentItemRelation
from fluent_contents.models.managers import ContentItemManager
from fluent_contents.rendering import render_placeholder
from fluent_contents.utils.filters import apply_filters
from future.utils import python_2_unicode_compatible

from bluebottle.utils.models import PublishableModel, get_language_choices
from bluebottle.utils.serializers import MLStripper
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


class DocumentItem(ContentItem):

    text = models.CharField(_('Link title'), max_length=100)
    document = models.FileField(
        _("Document"),
        upload_to='pages',
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=[
                    'application/pdf',
                    'application/zip',
                    'image/jpeg',
                    'image/png',
                    'image/gif',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ]
            ),
            validate_file_infection
        ]
    )

    def __str__(self):
        return Truncator(strip_tags(self.text)).words(20)

    class Meta(object):
        verbose_name = _('Document')
        verbose_name_plural = _('Document')


class ActionItem(ContentItem):

    link = models.CharField(_('link'), max_length=200)
    title = models.CharField(_('title'), max_length=100)

    def __str__(self):
        return Truncator(strip_tags(self.title)).words(20)

    class Meta(object):
        verbose_name = _('Call to action')
        verbose_name_plural = _('Call to actions')


class ColumnsItem(ContentItem):
    """
    A snippet of HTML text to display on a page.
    """
    text1 = PluginHtmlField(_('text left'), blank=True)
    text1_final = models.TextField(editable=False, blank=True, null=True)
    text2 = PluginHtmlField(_('text right'), blank=True)
    text2_final = models.TextField(editable=False, blank=True, null=True)

    objects = ContentItemManager()

    class Meta(object):
        verbose_name = _('Text in columns')
        verbose_name_plural = _('Text in columns')

    def __str__(self):
        return Truncator(strip_tags(self.text1)).words(20)

    def full_clean(self, *args, **kwargs):
        # This is called by the form when all values are assigned.
        # The pre filters are applied here, so any errors also appear as ValidationError.
        super(ColumnsItem, self).full_clean(*args, **kwargs)

        self.text1, self.text1_final = apply_filters(self, self.text1, field_name='text1')
        if self.text1_final == self.text1:
            # No need to store duplicate content:
            self.text1_final = None

        self.text2, self.text2_final = apply_filters(self, self.text2, field_name='text2')
        if self.text2_final == self.text2:
            # No need to store duplicate content:
            self.text2_final = None


class ImageTextItem(ContentItem):
    """
    A snippet of HTML text to display on a page.
    """
    text = PluginHtmlField(_('text'), blank=True)
    text_final = models.TextField(editable=False, blank=True, null=True)
    image = PluginImageField(
        _("Image"),
        upload_to='pages',
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    ALIGN_CHOICES = (
        ('left', _("Left")),
        ('right', _("Right")),
    )

    RATIO_CHOICES = (
        (8, _("2:1 (Text twice as wide)")),
        (6, _("1:1 (Equal width)")),
        (4, _("1:2 (Image twice as wide)")),
    )

    align = models.CharField(_("Picture placement"), max_length=10, choices=ALIGN_CHOICES, blank=True)
    ratio = models.IntegerField(_("Picture / Text ratio"), choices=RATIO_CHOICES, default=6, blank=True)
    objects = ContentItemManager()

    @property
    def text_width(self):
        return self.ratio

    @property
    def image_width(self):
        return 12 - self.text_width

    class Meta(object):
        verbose_name = _('Picture + Text')
        verbose_name_plural = _('Picture + Text')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/image-text'

    def __str__(self):
        return Truncator(strip_tags(self.text)).words(20)

    def full_clean(self, *args, **kwargs):
        # This is called by the form when all values are assigned.
        # The pre filters are applied here, so any errors also appear as ValidationError.
        super(ImageTextItem, self).full_clean(*args, **kwargs)

        self.text, self.text_final = apply_filters(self, self.text, field_name='text')
        if self.text_final == self.text:
            # No need to store duplicate content:
            self.text_final = None


class ImageTextRoundItem(ContentItem):
    text = PluginHtmlField(_('text'), blank=True)
    text_final = models.TextField(editable=False, blank=True, null=True)
    image = PluginImageField(
        _("Image"),
        upload_to='pages',
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    objects = ContentItemManager()

    class Meta(object):
        verbose_name = _('Text + Round Image')
        verbose_name_plural = _('Text + Round Image')

    def __str__(self):
        return Truncator(strip_tags(self.text)).words(20)

    def full_clean(self, *args, **kwargs):
        # This is called by the form when all values are assigned.
        # The pre filters are applied here, so any errors also appear as ValidationError.
        super(ImageTextRoundItem, self).full_clean(*args, **kwargs)

        self.text, self.text_final = apply_filters(self, self.text, field_name='text')
        if self.text_final == self.text:
            # No need to store duplicate content:
            self.text_final = None


@python_2_unicode_compatible
class Page(PublishableModel):
    class PageStatus(DjangoChoices):
        published = ChoiceItem('published', label=_('Published'))
        draft = ChoiceItem('draft', label=_('Draft'))

    title = models.CharField(_('Title'), max_length=200)
    slug = models.SlugField(_('Slug'), unique=False)
    full_page = models.BooleanField(
        _('Page without sub-navigation'),
        default=False,
        help_text=_('Show this page in full width and hide the sub-navigation')
    )

    show_title = models.BooleanField(
        default=True,
        help_text=_('Show the title of this page in the header')
    )

    # Contents
    language = models.CharField(
        _('language'),
        max_length=7,
        choices=lazy(get_language_choices, list)()
    )

    body = PlaceholderField('blog_contents', plugins=[
        'TextPlugin',
        'ColumnsPlugin',
        'ActionPlugin',
        'ImageTextPlugin',
        'ImageTextRoundPlugin',
        'OEmbedPlugin',
        'RawHtmlPlugin',
        'PicturePlugin',
        'DocumentPlugin'
    ])
    # This should not be nessecary, but fixes deletion of some pages
    # See https://github.com/edoburu/django-fluent-contents/issues/19
    contentitem_set = ContentItemRelation()

    @property
    def content(self):
        return self.body

    class Meta(object):
        ordering = ('language', 'slug')
        unique_together = ('language', 'slug')

        permissions = (
            ('api_read_page', 'Can view pages through the API'),
            ('api_add_page', 'Can add pages through the API'),
            ('api_change_page', 'Can change pages through the API'),
            ('api_delete_page', 'Can delete pages through the API'),
        )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f'/pages/{self.slug}'

    def get_meta_description(self, **kwargs):
        request = kwargs.get('request')
        s = MLStripper()
        s.feed(mark_safe(render_placeholder(request, self.body).html))
        return truncatechars(s.get_data(), 200)
