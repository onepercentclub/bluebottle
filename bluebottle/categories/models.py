from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from bluebottle.clients import properties
from bluebottle.utils.fields import ImageField
from adminsortable.admin import SortableMixin


class Category(models.Model):
    title = models.CharField(_("name"), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_("description"))
    image = ImageField(_("image"), max_length=255, upload_to='categories/',
                       help_text=_("Category image"))
    image_logo = ImageField(_("logo"), max_length=255, blank=True, null=True, upload_to='categories/logos/',
                            help_text=_("Category Logo image"))

    class Meta:
        ordering = ('title', )
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ['title']
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

    @property
    def projects(self):
        return self.project_set\
            .order_by('-favorite')\
            .filter(status__slug__in=['campaign', 'done-complete', 'done-incomplete', 'voting', 'voting-done'])


class CategoryContent(SortableMixin):
    category = models.ForeignKey(Category, related_name='contents')
    title = models.CharField(_('title'), max_length=60, help_text=_("Max: %(chars)s characters.") % {'chars': 60})
    description = models.TextField(_('description'),
                                   max_length=190,
                                   blank=True,
                                   default='',
                                   help_text=_("Max: %(chars)s characters.") % {'chars': 190})
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
    link_text = models.CharField(_("link name"),
                                 max_length=60,
                                 blank=True,
                                 default=_("Read more"),
                                 help_text=_("The link will only be displayed if an URL is provided. "
                                             "Max: %(chars)s characters.") % {'chars': 60})
    link_url = models.URLField(_("link url"), blank=True)
    sequence = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        verbose_name = _("content block")
        verbose_name_plural = _("content blocks")
        ordering = ['sequence']

    def __unicode__(self):
        return self.title
