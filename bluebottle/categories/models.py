from builtins import object

from adminsortable.admin import SortableMixin
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible
from parler.models import TranslatableModel, TranslatedFields

from bluebottle.utils.fields import ImageField
from bluebottle.utils.utils import get_current_host, get_current_language
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


@python_2_unicode_compatible
class Category(TranslatableModel):
    slug = models.SlugField(_('slug'), max_length=100, unique=True)

    image = ImageField(
        _("image"), max_length=255, blank=True, null=True,
        upload_to='categories/',
        help_text=_("Category image"),

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    image_logo = ImageField(
        _("logo"), max_length=255, blank=True, null=True,
        upload_to='categories/logos/',
        help_text=_("Category Logo image"),

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    translations = TranslatedFields(
        title=models.CharField(_("name"), max_length=255),
        description=models.TextField(_("description"))
    )

    class Meta(object):
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        # ordering = ['title']
        permissions = (
            ('api_read_category', 'Can view categories through API'),
        )

    class JSONAPIMeta:
        resource_name = 'pages/blocks/categories/categories'

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super(Category, self).save(**kwargs)

    def get_absolute_url(self):
        domain = get_current_host()
        language = get_current_language()
        return u"{}/{}/categories/{}/{}/activities/list".format(
            domain, language,
            self.pk,
            self.slug
        )


@python_2_unicode_compatible
class CategoryContent(SortableMixin, TranslatableModel):
    category = models.ForeignKey(Category, related_name='contents', on_delete=models.CASCADE)

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

    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta(object):
        verbose_name = _("content block")
        verbose_name_plural = _("content blocks")
        ordering = ['sequence']

    def __str__(self):
        return self.title
