from random import randrange

from future import standard_library
from rest_framework_json_api.relations import HyperlinkedRelatedField

standard_library.install_aliases()
import logging
import os
from os.path import isfile
import sys
from urllib.error import URLError
import urllib.parse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template import defaultfilters

from micawber.contrib.mcdjango import providers
from micawber.exceptions import ProviderException
from micawber.parsers import standalone_url_re, full_handler
from rest_framework import serializers
from sorl.thumbnail.shortcuts import get_thumbnail

from bluebottle.utils.utils import reverse_signed

logger = logging.getLogger(__name__)


def is_absolute_url(url):
    return bool(urllib.parse.urlparse(url).netloc)


class RestrictedImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if data.content_type not in settings.IMAGE_ALLOWED_MIME_TYPES:
            # We restrict images to a fixed set of mimetypes.
            # This prevents users from uploading broken eps files (for example),
            # that bring the application down.
            raise ValidationError(self.error_messages['invalid_image'])

        return super(RestrictedImageField, self).to_internal_value(data)


class SorlImageField(RestrictedImageField):
    def __init__(
        self, geometry_string, crop="center", colorspace="RGB", upscale=True, **kwargs
    ):
        self.geometry_string = geometry_string
        self.sorl_options = {"crop": crop, "colorspace": colorspace, "upscale": upscale}

        super(SorlImageField, self).__init__(**kwargs)

    def to_representation(self, value):
        if not value:
            return ""

        if not value.name:
            return ""

        if not os.path.exists(value.path):
            if settings.DEBUG and settings.RANDOM_IMAGE_PROVIDER:
                (width, height) = self.geometry_string.split('x')
                return settings.RANDOM_IMAGE_PROVIDER.format(seed=randrange(1, 300), width=width, height=height)
            return ""

        _, ext = os.path.splitext(value.path)
        if ext == '.svg':
            return value.url

        if ext == '.png':
            self.sorl_options['format'] = 'PNG'

        # The get_thumbnail() helper doesn't respect the THUMBNAIL_DEBUG setting
        # so we need to deal with exceptions like is done in the template tag.
        try:
            thumbnail = get_thumbnail(value, self.geometry_string, **self.sorl_options)
        except IOError:
            return ""
        except Exception:
            if getattr(settings, 'THUMBNAIL_DEBUG', None):
                raise
            logger.error('Thumbnail failed:', exc_info=sys.exc_info())
            return ""
        relative_url = settings.MEDIA_URL + thumbnail.name
        return relative_url


class OEmbedField(serializers.Field):
    def __init__(self, source, maxwidth=None, maxheight=None, **kwargs):
        super(OEmbedField, self).__init__(source)
        self.params = getattr(settings, 'MICAWBER_DEFAULT_SETTINGS', {})
        self.params.update(kwargs)
        # enforce HTTPS, see https://groups.google.com/forum/?fromgroups
        # #!topic/youtube-api-gdata/S9Fa-Zw2Ma8
        self.params['scheme'] = 'https'
        if maxwidth and maxheight:
            self.params['maxwidth'] = maxwidth
            self.params['maxheight'] = maxheight
        elif maxwidth:
            self.params['maxwidth'] = maxwidth
            self.params.pop('maxheight', None)

    def to_representation(self, value):
        if not value or not standalone_url_re.match(value):
            return ""
        url = value.strip()
        if value == 'https://vimeo.com/85425318':
            return "<iframe src=\"//player.vimeo.com/video/85425318\" " \
                   "hard=\"code\" width=\"1024\" height=\"576\" " \
                   "frameborder=\"0\" title=\"How it works - Cares\" " \
                   "webkitallowfullscreen mozallowfullscreen " \
                   "allowfullscreen></iframe>"
        try:
            response = providers.request(url, **self.params)
        except ProviderException:
            return ""
        except URLError:
            return ""
        else:
            html = full_handler(url, response, **self.params)
            # Tweak for youtube to hide controls and info bars.
            html = html.replace('feature=oembed',
                                'feature=oembed&showinfo=0&controls=0')
            return html


class FileSerializer(serializers.FileField):
    def to_representation(self, value):
        if value:
            try:
                return {'name': os.path.basename(value.name),
                        'url': value.url,
                        'size': defaultfilters.filesizeformat(value.size)}
            except OSError:
                return {'name': '',
                        'url': '',
                        'size': ''}

        else:
            return {'name': '',
                    'url': '',
                    'size': ''}


class ImageSerializer(RestrictedImageField):
    crop = 'center'

    def to_representation(self, value):
        if not value:
            return None

        # The get_thumbnail() helper doesn't respect the THUMBNAIL_DEBUG setting
        # so we need to deal with exceptions like is done in the template tag.
        if not isfile(value.path):
            return None
        try:
            large = settings.MEDIA_URL + get_thumbnail(value, '800x450', crop=self.crop).name
            full = settings.MEDIA_URL + get_thumbnail(value, '1200x900').name
            small = settings.MEDIA_URL + get_thumbnail(value, '400x300', crop=self.crop).name
            square = settings.MEDIA_URL + get_thumbnail(value, '600x600', crop=self.crop).name
            wide = settings.MEDIA_URL + get_thumbnail(value, '1024x256', crop=self.crop).name
            original = settings.MEDIA_URL + get_thumbnail(value, '1920', upscale=False).name

        except Exception:
            if getattr(settings, 'THUMBNAIL_DEBUG', None):
                raise
            logger.error('Thumbnail failed:', exc_info=sys.exc_info())
            return None
        request = self.context.get('request')
        if request:
            return {
                'full': request.build_absolute_uri(full),
                'large': request.build_absolute_uri(large),
                'small': request.build_absolute_uri(small),
                'square': request.build_absolute_uri(square),
                'wide': request.build_absolute_uri(wide),
                'original': request.build_absolute_uri(original),
            }
        return {'full': full, 'large': large, 'small': small, 'square': square, 'original': original}


class PhotoSerializer(RestrictedImageField):
    crop = 'center'

    def to_representation(self, value):
        if not value:
            return None

        # The get_thumbnail() helper doesn't respect the THUMBNAIL_DEBUG setting
        # so we need to deal with exceptions like is done in the template tag.
        try:
            full = settings.MEDIA_URL + get_thumbnail(value, '800x600').name
            small = settings.MEDIA_URL + get_thumbnail(value, '120x120', crop=self.crop).name
        except Exception:
            if getattr(settings, 'THUMBNAIL_DEBUG', None):
                raise
            logger.error('Thumbnail failed:', exc_info=sys.exc_info())
            return None
        request = self.context.get('request')
        if request:
            return {
                'full': request.build_absolute_uri(full),
                'small': request.build_absolute_uri(small),
            }
        return {'full': full, 'small': small}


class PrivateFileSerializer(FileSerializer):
    def __init__(
        self, url_name, file_attr=None, filename=None, url_args=None,
        permission=None, *args, **kwargs
    ):
        self.url_name = url_name
        self.url_args = url_args or []
        self.permission = permission

        if file_attr and filename:
            raise ValueError('Either set the field or the filename, not both')

        self.file_attr = file_attr
        self.filename = filename

        super(PrivateFileSerializer, self).__init__(*args, **kwargs)

    def get_attribute(self, value):
        return value  # Just pass the whole object back

    def to_representation(self, value):
        """
        Return a signed url
        """
        permission = self.permission()

        if not (
            permission.has_object_action_permission(
                'GET', self.context['request'].user, value
            ) and permission.has_action_permission(
                'GET', self.context['request'].user, value.__class__
            )
        ):
            return None

        url_args = [getattr(value, arg) for arg in self.url_args]
        url = reverse_signed(self.url_name, args=url_args)

        if self.filename:
            filename = self.filename
        elif self.file_attr:
            file = getattr(value, self.file_attr, None)
            if not file:
                return None
            else:
                filename = os.path.basename(file.name)
        else:
            filename = '---'

        return {
            'url': url,
            'name': filename
        }


class CustomHyperlinkRelatedSerializer(HyperlinkedRelatedField):

    def __init__(self, link=None, **kwargs):
        self.link = link
        super(CustomHyperlinkRelatedSerializer, self).__init__(source='parent', read_only=True, **kwargs)

    def get_links(self, *args, **kwargs):
        return {
            'related': self.link
        }
