from adminsortable.admin import SortableMixin
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

from bluebottle.clients import properties
from bluebottle.files.validators import validate_video_file_size
from bluebottle.utils.fields import ImageField
from bluebottle.utils.validators import FileMimetypeValidator


class Category(TranslatableModel):
    slug = models.SlugField(_('slug'), max_length=100, unique=True)

    image = ImageField(
        _("image"), max_length=255, blank=True, null=True,
        upload_to='categories/',
        help_text=_("Category image"))
    video = models.FileField(
        _("video"), max_length=255,
        blank=True, null=True,
        validators=[
            validate_video_file_size,
            FileMimetypeValidator(
                allowed_mimetypes=settings.VIDEO_FILE_ALLOWED_MIME_TYPES
            )
        ],
        help_text=_('This video will autoplay at the background. '
                    'Allowed types are mp4, ogg, 3gp, avi, mov and webm. '
                    'File should be smaller then 10MB.'),
        upload_to='banner_slides/')
    image_logo = ImageField(
        _("logo"), max_length=255, blank=True, null=True,
        upload_to='categories/logos/',
        help_text=_("Category Logo image"))

    translations = TranslatedFields(
        title=models.CharField(_("name"), max_length=255),
        description=models.TextField(_("description"))
    )

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        # ordering = ['title']
        permissions = (
            ('api_read_category', 'Can view categories through API'),
        )

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super(Category, self).save(**kwargs)

    def get_absolute_url(self):
        return 'https://{}/projects/?category={}'.format(properties.tenant.domain_url, self.slug)


class CategoryContent(SortableMixin, TranslatableModel):
    category = models.ForeignKey(Category, related_name='contents')

    translations = TranslatedFields(
        title=models.CharField(
            _('title'),
            max_length=60,
            help_text=_("Max: %(chars)s characters.") % {'chars': 60}
        ),
        description=models.TextField(
            _('description'),
            max_length=190,
            blank=True,
            default='',
            help_text=_("Max: %(chars)s characters.") % {'chars': 190}
        ),
        link_text=models.CharField(
            _("link name"),
            max_length=60,
            blank=True,
            default=_("Read more"),
            help_text=_("The link will only be displayed if an URL is provided. "
                        "Max: %(chars)s characters.") % {'chars': 60}
        ),
        link_url=models.CharField(
            _("link url"),
            max_length=300,
            blank=True
        )
    )

    image = ImageField(_('image'),
                       max_length=255,
                       blank=True,
                       null=True,
                       upload_to='categories/content/',
                       help_text=_("Accepted file format: .jpg, .jpeg & .png"))
    video_url = models.URLField(max_length=100,
                                blank=True,
                                default='',
                                help_text=_("Setting a video url will replace the image. Only YouTube or Vimeo videos "
                                            "are accepted. Max: %(chars)s characters.") % {'chars': 100})
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        verbose_name = _("content block")
        verbose_name_plural = _("content blocks")
        ordering = ['sequence']

    def __unicode__(self):
        return self.title
