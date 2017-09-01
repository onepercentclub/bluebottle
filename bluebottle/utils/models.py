import sys

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings

import bluebottle.utils.monkey_patch_migration  # noqa
import bluebottle.utils.monkey_patch_corsheaders  # noqa
import bluebottle.utils.monkey_patch_parler  # noqa


class Language(models.Model):
    """
    A language - ISO 639-1
    """
    code = models.CharField(max_length=2, blank=False)
    language_name = models.CharField(max_length=100, blank=False)
    native_name = models.CharField(max_length=100, blank=False)

    class Meta:
        ordering = ['language_name']

    def __unicode__(self):
        return self.language_name


class Address(models.Model):
    """
    A postal address.
    """
    line1 = models.CharField(max_length=100, blank=True)
    line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.ForeignKey('geo.Country', blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.line1[:80]


# Below is test-only stuff
INCLUDE_TEST_MODELS = getattr(settings, 'INCLUDE_TEST_MODELS', False)

if 'test' in sys.argv or 'jenkins' in sys.argv or INCLUDE_TEST_MODELS:
    import re

    from fluent_contents.models import PlaceholderField
    from fluent_contents.plugins.oembeditem.models import OEmbedItem
    from bluebottle.contentplugins.models import PictureItem

    class MetaDataModel(models.Model):
        """
        This is a model purely for MetaData testing in the API.
        """
        title = models.CharField(max_length=50)
        contents = PlaceholderField("blog_contents")

        def get_first_image(self, **kwargs):
            """
            Get all the content items and filter out those that are pictures.
            Return the url of the first picture.
            """
            relevant_items = [item for item in self.contents.get_content_items()
                              if (
                                  isinstance(item, PictureItem) or isinstance(
                                      item,
                                      OEmbedItem))]

            item = relevant_items.pop(0)
            if isinstance(item, PictureItem):
                # we're sure we are dealing with a picture, so just return the image url
                request = kwargs.get('request')
                location = item.image.url
                absolute_uri = request.build_absolute_uri(location)
                return (absolute_uri, True)

            else:
                # it's an OEmbedItem. check if's an image suitable for facebook OG
                # https://developers.facebook.com/docs/web/tutorials/scrumptious/open-graph-object/
                # Only JPEG, PNG, GIF and BMP images are supported
                # TODO: a generic utils function for this kind of stuff would be nice ;)
                regex = re.compile(
                    r'http(s?)://.*/.*\.(png|jpg|jpeg|jpe|jfif|jif|jfi|gif|bmp|dib)',
                    re.IGNORECASE)
                match = re.match(regex, item.url)
                while relevant_items and not match:
                    item = relevant_items.pop(0)
                    match = re.match(regex, item.url)

                if match:
                    # huray, we found a suitable image!
                    return (item.url, True)
            return None

        def get_image_without_is_url(self, **kwargs):
            """ Return an image to be serialized """
            relevant_items = [item for item in self.contents.get_content_items()
                              if isinstance(item, PictureItem)]
            item = relevant_items.pop(0)
            return item.image


class MailLog(models.Model):

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    type = models.CharField(max_length=200)

    created = models.DateTimeField(auto_now_add=True)
