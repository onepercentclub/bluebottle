import logging
import os
from os.path import isfile
import re
import sys
from urllib2 import URLError

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.template import defaultfilters
from django.template.defaultfilters import linebreaks
from django.utils.encoding import smart_str
from django.utils.html import strip_tags, urlize

from micawber.contrib.mcdjango import providers
from micawber.exceptions import ProviderException
from micawber.parsers import standalone_url_re, full_handler
from rest_framework import serializers
from sorl.thumbnail.shortcuts import get_thumbnail

logger = logging.getLogger(__name__)


class RestrictedImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if data.content_type not in settings.IMAGE_ALLOWED_MIME_TYPES:
            # We restrict images to a fixed set of mimetypes.
            # This prevents users from uploading broken eps files (for example),
            # that bring the application down.
            raise ValidationError(self.error_messages['invalid_image'])

        return super(RestrictedImageField, self).to_internal_value(data)


class SorlImageField(RestrictedImageField):
    def __init__(self, geometry_string, crop='center',
                 colorspace='RGB', watermark=None, watermark_pos=None,
                 watermark_size=None, **kwargs):
        self.geometry_string = geometry_string
        self.sorl_options = {
            'crop': crop,
            'colorspace': colorspace,
        }

        if watermark:
            self.sorl_options['watermark'] = watermark
            self.sorl_options['watermark_pos'] = watermark_pos
            self.sorl_options['watermark_size'] = watermark_size

        super(SorlImageField, self).__init__(**kwargs)

    def to_representation(self, value):
        if not value:
            return ""

        if not value.name:
            return ""

        if not os.path.exists(value.path):
            return ""

        if 'watermark' in self.sorl_options:
            try:
                self.sorl_options['watermark'] = self.sorl_options['watermark']()
            except TypeError:
                pass

        # The get_thumbnail() helper doesn't respect the THUMBNAIL_DEBUG setting
        # so we need to deal with exceptions like is done in the template tag.
        try:
            thumbnail = unicode(get_thumbnail(value, self.geometry_string, **self.sorl_options))
        except IOError:
            return ""
        except Exception:
            if getattr(settings, 'THUMBNAIL_DEBUG', None):
                raise
            logger.error('Thumbnail failed:', exc_info=sys.exc_info())
            return ""
        relative_url = settings.MEDIA_URL + thumbnail
        return relative_url


class ContentTextField(serializers.CharField):
    """
    A serializer for content text such as text field found in Reaction and
    TextWallpost. This serializer creates clickable links for text urls and
    adds <br/> and/or <p></p> in-place of new line characters.
    """

    def to_representation(self, value):
        # Convert model instance text -> text for reading.
        text = super(ContentTextField, self).to_representation(value)
        # This is equivalent to the django template filter:
        # '{{ value|urlize|linebreaks }}'. Note: Text from the
        # database is escaped again here (on read) just as a
        # double check for HTML / JS injection.
        text = linebreaks(urlize(text, None, True, True))
        # This ensure links open in a new window (BB-136).
        return re.sub(r'<a ', '<a target="_blank" ', text)

    def to_internal_value(self, value):
        # Convert text -> model instance text for writing.
        text = super(ContentTextField, self).to_internal_value(value)
        # HTML tags are stripped and any HTML / JS that is left is escaped.
        return strip_tags(text)


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


class PrimaryKeyGenericRelatedField(serializers.RelatedField):
    """ A field serializer for the object_id field in a GenericForeignKey. """

    read_only = False

    def __init__(self, to_model, *args, **kwargs):
        self.to_model = to_model
        queryset = self.to_model.objects.order_by('id').all()
        super(PrimaryKeyGenericRelatedField, self).__init__(queryset=queryset)

    def label_from_instance(self, obj):
        return "{0} - {1}".format(smart_str(self.to_model.__unicode__(obj)),
                                  str(obj.id))

    def prepare_value(self, obj):
        # Called when preparing the ChoiceField widget from the to_model queryset.
        return obj.serializable_value('id')

    def to_representation(self, obj):
        # Serialize using self.source (i.e. 'object_id').
        return obj.serializable_value(self.source)

    def to_internal_value(self, value):
        try:
            to_instance = self.to_model.objects.get(pk=value)
        except self.to_model.DoesNotExist:
            raise ValidationError(self.error_messages['invalid'])
        else:
            return to_instance.id


class SlugGenericRelatedField(serializers.RelatedField):
    """
    A field serializer for the object_id field in a GenericForeignKey
    based on the related model slug.
    """

    read_only = False

    def __init__(self, to_model, *args, **kwargs):
        self.to_model = to_model
        queryset = self.to_model.objects.order_by('id').all()
        super(SlugGenericRelatedField, self).__init__(*args, source='object_id',
                                                      queryset=queryset,
                                                      **kwargs)

    def label_from_instance(self, obj):
        return "{0} - {1}".format(smart_str(self.to_model.__unicode__(obj)),
                                  obj.slug)

    def prepare_value(self, to_instance):
        # Called when preparing the ChoiceField widget from the to_model queryset.
        return to_instance.serializable_value('slug')

    def to_representation(self, obj):
        # Serialize using self.source (i.e. 'object_id').
        try:
            to_instance = self.to_model.objects.get(
                id=getattr(obj, self.source))
        except self.to_model.DoesNotExist:
            return None
        return to_instance.serializable_value('slug')

    def to_internal_value(self, value):
        try:
            to_instance = self.to_model.objects.get(slug=value)
        except self.to_model.DoesNotExist:
            raise ValidationError(self.error_messages['invalid'])
        else:
            return to_instance.id


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
            large = settings.MEDIA_URL + unicode(
                get_thumbnail(value, '800x450', crop=self.crop))
            full = settings.MEDIA_URL + unicode(
                get_thumbnail(value, '1200x900'))
            small = settings.MEDIA_URL + unicode(
                get_thumbnail(value, '400x300', crop=self.crop))
            square = settings.MEDIA_URL + unicode(
                get_thumbnail(value, '600x600', crop=self.crop))
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
            }
        return {'full': full, 'large': large, 'small': small, 'square': square}


class PhotoSerializer(RestrictedImageField):
    crop = 'center'

    def to_representation(self, value):
        if not value:
            return None

        # The get_thumbnail() helper doesn't respect the THUMBNAIL_DEBUG setting
        # so we need to deal with exceptions like is done in the template tag.
        try:
            full = settings.MEDIA_URL + unicode(get_thumbnail(value, '800x600'))
            small = settings.MEDIA_URL + unicode(
                get_thumbnail(value, '120x120', crop=self.crop))
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
    def field_to_native(self, obj, field_name):
        if not obj:
            return None
        value = getattr(obj, self.source or field_name)
        if not value:
            return None
        content_type = ContentType.objects.get_for_model(
            self.parent.Meta.model).id
        pk = obj.pk
        url = reverse('document_download_detail',
                      kwargs={'content_type': content_type, 'pk': pk})
        return {'name': os.path.basename(value.name),
                'url': url}
