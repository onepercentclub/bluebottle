from builtins import object
from django.conf import settings
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from fluent_contents.models import PlaceholderField, ContentItemRelation
from fluent_contents.rendering import render_placeholder
from future.utils import python_2_unicode_compatible

from bluebottle.utils.fields import ImageField
from bluebottle.utils.models import PublishableModel, get_language_choices
from bluebottle.utils.serializers import MLStripper
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


@python_2_unicode_compatible
class NewsItem(PublishableModel):

    title = models.CharField(_("Title"), max_length=200)
    slug = models.SlugField(_("Slug"))

    # Contents
    main_image = ImageField(
        _("Main image"),
        help_text=_("Shows at the top of your post."),
        upload_to='blogs', blank=True,

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )
    language = models.CharField(_("language"),
                                max_length=7,
                                choices=lazy(get_language_choices, list)())
    contents = PlaceholderField("blog_contents", plugins=[
        'TextPlugin',
        'ImageTextPlugin',
        'OEmbedPlugin',
        'RawHtmlPlugin',
        'PicturePlugin'
    ])
    # This should not be necessary, but fixes deletion of some news items
    # See https://github.com/edoburu/django-fluent-contents/issues/19
    contentitem_set = ContentItemRelation()

    allow_comments = models.BooleanField(_("Allow comments"), default=True)

    def __str__(self):
        return self.title

    def get_meta_description(self, **kwargs):
        request = kwargs.get('request')
        s = MLStripper()
        s.feed(mark_safe(render_placeholder(request, self.contents).html))
        return truncatechars(s.get_data(), 250)

    class Meta(object):
        verbose_name = _("news item")
        verbose_name_plural = _("news items")

        permissions = (
            ('api_read_newsitem', 'Can view news items through the API'),
            ('api_add_newsitem', 'Can add news items through the API'),
            ('api_change_newsitem', 'Can change news items through the API'),
            ('api_delete_newsitem', 'Can delete news items through the API'),
        )
