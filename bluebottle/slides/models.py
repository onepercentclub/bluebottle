from django.conf import settings
from django.db import models
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem

from bluebottle.clients import properties
from bluebottle.files.validators import validate_video_file_size
from bluebottle.utils.fields import ImageField
from bluebottle.utils.models import PublishableModel
from bluebottle.utils.validators import FileMimetypeValidator


def get_languages():
    return properties.LANGUAGES


class Slide(PublishableModel):
    """
    Slides for homepage
    """

    class SlideStatus(DjangoChoices):
        published = ChoiceItem('published', label=_("Published"))
        draft = ChoiceItem('draft', label=_("Draft"))

    slug = models.SlugField(_("Slug"))
    language = models.CharField(
        _("language"), max_length=5,
        choices=lazy(get_languages, tuple)())
    tab_text = models.CharField(
        _("Tab text"), max_length=100,
        help_text=_("This is shown on tabs beneath the banner."))

    # Contents
    title = models.CharField(_("Title"), max_length=100, blank=True)
    body = models.TextField(_("Body text"), blank=True)
    image = ImageField(
        _("Image"), max_length=255,
        blank=True, null=True,
        upload_to='banner_slides/')
    background_image = ImageField(
        _("Background image"), max_length=255,
        blank=True, null=True,
        upload_to='banner_slides/')
    video = models.FileField(
        _("Video"), max_length=255,
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
    video_url = models.URLField(
        _("Video url"),
        max_length=100, blank=True,
        default='')
    link_text = models.CharField(
        _("Link text"), max_length=400, blank=True,
        help_text=_("This is the text on the button inside the banner."))
    link_url = models.CharField(
        _("Link url"), max_length=400, blank=True,
        help_text=_("This is the link for the button inside the banner."))
    style = models.CharField(
        _("Style"), max_length=40,
        help_text=_("Styling class name"),
        default='default', blank=True)

    # Metadata
    sequence = models.IntegerField()

    @property
    def background_image_full_path(self):
        return "{0}{1}".format(settings.MEDIA_URL, str(self.background_image))

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('language', 'sequence')
