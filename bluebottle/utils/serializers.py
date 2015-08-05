import sys
import re

from django.conf import settings
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.template.defaultfilters import truncatechars
from django.utils.importlib import import_module
from django_tools.middlewares import ThreadLocal

from rest_framework import serializers
from rest_framework.serializers import get_component
from taggit.managers import _TaggableManager

from bluebottle.bluebottle_drf2.serializers import ImageSerializer

from .validators import validate_postal_code
from .models import Address, Language

from HTMLParser import HTMLParser


class ShareSerializer(serializers.Serializer):
    share_name = serializers.CharField(max_length=256, required=True)
    share_email = serializers.EmailField(required=True)
    share_motivation = serializers.CharField(default="", required=True)
    share_cc = serializers.BooleanField(default=False, required=True)

    project = serializers.CharField(max_length=256, required=True)


class LanguageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Language
        fields = ('id', 'code', 'language_name', 'native_name')


class MLStripper(HTMLParser):
    """ Used to strip HTML tags for meta fields (e.g. description) """
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


class AddressSerializer(serializers.ModelSerializer):

    def validate_postal_code(self, attrs, source):
        value = attrs[source]
        if value:
            country_code = ''
            if 'country' in attrs:
                country_code = attrs['country']
            elif self.object and self.object.country:
                country_code = self.object.country.alpha2_code

            if country_code:
                validate_postal_code(value, country_code)
        return attrs

    class Meta:
        model = Address
        fields = ('id', 'line1', 'line2', 'city', 'state', 'country', 'postal_code')



SCHEME_PATTERN = r'^https?://'

class URLField(serializers.URLField):
    """ URLField allowing absence of url scheme """

    def from_native(self, value):
        """ Allow exclusion of http(s)://, add it if it's missing """
        if not value:
            return value
        m = re.match(SCHEME_PATTERN, value)
        if not m: # no scheme
            value = "http://%s" % value
        return value


class MetaField(serializers.Field):
    """
    Serializer field which fills meta data based on model attributes
    Init with `field = None` to disable the field.

    Callables need to accept **kwargs, as the request is sent by default.

    Usage example:

    #models.py
    class Example(models.Model):
        title = models.CharField(max_length=50)

        def get_description(self, **kwargs):
            return self.title + ' (description)'


    # serializers.py
    class ExampleSerializer(serializers.ModelSerializer):

        meta_data = MetaField(
                title = 'title',
                description = 'get_description',
                keywords = None,
                image_source = None
            )

        class Meta:
            model = Example
            fields = ('title', 'meta_data')


    This returns API JSON as:

    json = {
        'title': 'Sample title',
        'meta_data': {
            'title': 'Sample title',
            'description': 'Sample title (description)',
            'keywords': null,
            'image': null
            }
        }
    }

    When image_source is provided, you get a JSON object with keys 'large',
    'small', 'full' and 'square'.

    Currently, images are only used for facebook
    """

    def __init__(self, title = 'title',
                description = 'description', keywords = 'tags',
                image_source = None,
                *args, **kwargs):

        # default to None, return the default title/image if no explicit title/image were provided
        self.fb_title = kwargs.pop('fb_title', None)
        self.tweet = kwargs.pop('tweet', None)
        self.url = kwargs.pop('url', None)
        # TODO: add support for list of image sources -> multiple images

        self.title = title
        self.description = description
        self.keywords = keywords
        self.image_source = image_source

        super(MetaField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        """ Get the parts of the meta dict """

        # set defaults
        value = {
            'title': None,
            'fb_title': None,
            'tweet': None,
            'description': None,
            'image': None,
            'keywords': None,
            'url': None,
        }

        # get the meta title from object callable or object property
        if self.title:
            title = self._get_callable(obj, self.title)
            if title is None:
                title = self._get_field(obj, self.title)
            value['title'] = title

        # try to get the facebook title
        if self.fb_title is not None:
            fb_title = self._get_callable(obj, self.fb_title)
            if fb_title is None:
                fb_title = self._get_field(obj, self.fb_title)
            value['fb_title'] = fb_title
        elif self.title:
            value['fb_title'] = value['title']

        if self.tweet is not None:
            tweet = self._get_callable(obj, self.tweet)
            if tweet is None:
                tweet = self._get_field(obj, self.tweet)
            value['tweet'] = tweet
        elif self.title:
            value['tweet'] = '{URL}'

        # get the meta description from object callable or object property
        if self.description:
            description = self._get_callable(obj, self.description)
            if description is None:
                description = self._get_field(obj, self.description)
                description = truncatechars(description, 200)
            value['description'] = description

        # keywords: either from object callable or property, if property,
        # check if we are referring to taggit tags.
        if self.keywords:
            keywords = self._get_callable(obj, self.keywords)
            if keywords is None:
                # Get the keywords
                keywords = self._get_field(obj, self.keywords)

                # usually tags as keywords
                if isinstance(keywords, _TaggableManager):
                    keywords = [tag.name.lower() for tag in keywords.all()]
                else:
                    # try to split the keywords
                    try:
                        keywords = keywords.lower().split()
                    except AttributeError:
                        keywords = ''
                value['keywords'] = ", ".join(keywords)
            else:
                value['keywords'] = keywords

        # special case with images, use the ImageSerializer to get cropped formats
        if self.image_source:
            """
            Sometimes, direct urls can be returned, and then we don't
            want to serialize the 'image'. It's also possible that only an
            image is returned without  is_url (e.g. directly from model attribute).
            """
            image_source = self._get_callable(obj, self.image_source)
            if image_source is None:
                image, is_url = self._get_field(obj, self.image_source), False
            else:
                try:
                    image, is_url = image_source[0], image_source[1]
                except TypeError: # no indexing, so not a tupple that was returned
                    image, is_url = image_source, False

            if is_url:
                # the callable returned a direct url, instead of a serializable image
                value['image'] = image
            else:
                serializer = ImageSerializer()
                serializer.context = self.context
                images = serializer.to_native(image)
                if images:
                    # always take the full image for facebook, they consume it and
                    # resize/store the images themselve
                    value['image'] = images.get('full', None)

        if self.url:
            url = self._get_callable(obj, self.url)
            if url is None:
                url = self._get_field(obj, self.url)
            value['url'] = url

        return self.to_native(value)


    def _get_field(self, obj, field_name):
        """ Allow traversing the relations tree for fields """
        attrs = field_name.split('__')

        field = obj
        # Just return None on errors so tests won't trip.
        for attr in attrs:
            try:
                field = getattr(field, attr)
            except ObjectDoesNotExist:
                return None
            except AttributeError:
                return None
        return field

    def _get_callable(self, obj, attr):
        """ Check if the attr is callable, return its value if it is """
        try:
            _attr = getattr(obj, attr)
            if callable(_attr):
                request = ThreadLocal.get_current_request()
                return _attr(request=request)
        except AttributeError: # not a model/object attribute or relation does not exist
            pass
        return None


class DefaultSerializerMixin(object):
    def get_custom_serializer(self):
        return self.model._meta.default_serializer

    def get_serializer_class(self):
        dotted_path = self.get_custom_serializer()
        bits = dotted_path.split('.')
        module_name = '.'.join(bits[:-1])
        module = import_module(module_name)
        cls_name = bits[-1]
        return getattr(module, cls_name)


class ManageSerializerMixin(DefaultSerializerMixin):
    def get_custom_serializer(self):
        return self.model._meta.manage_serializer


class PreviewSerializerMixin(DefaultSerializerMixin):
    def get_custom_serializer(self):
        return self.model._meta.preview_serializer


class HumanReadableChoiceField(serializers.ChoiceField):
    def field_to_native(self, obj, field_name):
        """
        Given and object and a field name, returns the value that should be
        serialized for that field. Display the choice label.
        """
        if obj is None:
            return self.empty

        if self.source == '*':
            return self.to_native(obj)

        source = self.source or field_name
        value = obj

        components = source.split('.')
        for component in components:
            if component == components[-1]: # last item, fetch human readable form
                component = 'get_{0}_display'.format(component)
            value = get_component(value, component)
            if value is None:
                break

        return self.to_native(value.lower())


#### TESTS #############
# Below is test-only stuff
INCLUDE_TEST_MODELS = getattr(settings, 'INCLUDE_TEST_MODELS', False)

if 'test' in sys.argv or INCLUDE_TEST_MODELS:

    from .models import MetaDataModel

    class MetaDataSerializer(serializers.ModelSerializer):

        meta_data = MetaField(
            description = None,
            image_source = None,
            keywords = 'tags'
            )

        class Meta:
            model = MetaDataModel
