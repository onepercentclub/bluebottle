"""
ContentItem models for custom django-fluent-contents plugins.
"""
from builtins import object

from future.utils import python_2_unicode_compatible

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem

from fluent_contents.models import ContentItem
from bluebottle.utils.fields import ImageField
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


@python_2_unicode_compatible
class PictureItem(ContentItem):
    """
    Picture content item
    """

    class PictureAlignment(DjangoChoices):
        float_left = ChoiceItem('float-left', label=_("Float left"))
        center = ChoiceItem('center', label=_("Center"))
        float_right = ChoiceItem('float-right', label=_("Float right"))

    image = ImageField(
        _("Picture"), upload_to='content_images',

        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )
    align = models.CharField(_("Align"), max_length=50,
                             choices=PictureAlignment.choices)

    class Meta(object):
        verbose_name = _("Picture")
        verbose_name_plural = _("Pictures")

    def __str__(self):
        return self.image.name if self.image else u'(no image)'

    class JSONAPIMeta:
        resource_name = 'pages/blocks/image'
