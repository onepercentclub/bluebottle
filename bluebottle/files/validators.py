from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_video_file_size(value):
    filesize = value.size

    if filesize > 10485760:
        raise ValidationError(_("Videos larger then 10MB will slow down the page too much."))
    else:
        return value
