from builtins import object
from builtins import str

from django.conf import settings
from django.db import models
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem
from future.utils import python_2_unicode_compatible

from bluebottle.files.validators import validate_video_file_size
from bluebottle.utils.fields import ImageField
from bluebottle.utils.models import PublishableModel, get_language_choices
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection


@python_2_unicode_compatible
class Slide(PublishableModel):
    """
    Slides for homepage
    """

    class SlideStatus(DjangoChoices):
        published = ChoiceItem('published', label=_("Published"))
        draft = ChoiceItem('draft', label=_("Draft"))

    slug = models.SlugField(_("Slug"))
    language = models.CharField(
        _("language"), max_length=7,
        choices=lazy(get_language_choices, list)())
    tab_text = models.CharField(
        _("Tab text"), max_length=100,
        help_text=_("This is shown on tabs beneath the banner."))

    # Contents
    title = models.CharField(_("Title"), max_length=72, blank=True)
    body = models.TextField(_("Body text"), max_length=140, blank=True)
    background_image = ImageField(
        _("Background image"), max_length=255,
        blank=True, null=True,
        help_text=_(
            "The ideal image will have an aspect ratio of 16:9 and be no larger than 2Mb. "
            "Sides of the image maybe cropped out on mobile screens."
        ),
        upload_to='banner_slides/',
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )
    video = models.FileField(
        _("Background video"), max_length=255,
        blank=True, null=True,
        validators=[
            validate_video_file_size,
            FileMimetypeValidator(
                allowed_mimetypes=settings.VIDEO_FILE_ALLOWED_MIME_TYPES
            )
        ],
        help_text=_(
            'This video will autoplay and loop in the background, '
            'without sound. Allowed formats are mp4, ogg, 3gp, avi, mov and webm. '
            'The file should be smaller than 10 MB. Adding a background video will '
            'replace the background image.'
        ),
        upload_to='banner_slides/')
    video_url = models.URLField(
        _("Video"),
        max_length=100, blank=True,
        help_text=_(
            "YouTube and Vimeo videos are supported, add the video by pasting their URL above. "
            "This will add a 'play' button to the slider. "
            "The video will play after the 'Play' button is selected."
        ),
        default='')
    link_text = models.CharField(
        _("Button label"), max_length=400, blank=True,
        help_text=_("This is the text displayed on the button."))
    link_url = models.CharField(
        _("Button URL"), max_length=400, blank=True,
        help_text=_("This is the URL to which the button links."))
    style = models.CharField(
        _("Style"), max_length=40,
        help_text=_("Styling class name"),
        default='default', blank=True)

    # Metadata
    sequence = models.IntegerField()

    @property
    def background_image_full_path(self):
        return "{0}{1}".format(settings.MEDIA_URL, str(self.background_image))

    def __str__(self):
        return self.title or str(_('-empty-'))

    class Meta(object):
        ordering = ('language', 'sequence')

    class JSONAPIMeta:
        resource_name = 'pages/blocks/slides/slides'
