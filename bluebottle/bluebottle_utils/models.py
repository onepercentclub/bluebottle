from django.conf import settings
from django.db import models


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

    def __unicode__(self):
        return self.line1[:80]

    class Meta:
        abstract = True


# Below is test-only stuff

INCLUDE_TEST_MODELS = getattr(settings, 'INCLUDE_TEST_MODELS', False)

if INCLUDE_TEST_MODELS:
    from django.template.defaultfilters import truncatechars


    from fluent_contents.models import PlaceholderField
    from fluent_contents.plugins.oembeditem.models import OEmbedItem
    from bluebottle.contentplugins.models import PictureItem
    from fluent_contents.rendering import render_placeholder
    from taggit_autocomplete_modified.managers import TaggableManagerAutocomplete as TaggableManager


    class MetaDataModel(models.Model):
        """
        This is a model purely for MetaData testing in the API.
        """
        title = models.CharField(max_length=50)
        tags = TaggableManager(blank=True)
        contents = PlaceholderField("blog_contents")


        def get_first_image(self, **kwargs):
            """
            Get all the content items and filter out those that are pictures.
            Return the url of the first picture.
            """
            relevant_items = [item for item in self.contents.get_content_items() \
                        if (isinstance(item, PictureItem) or isinstance(item, OEmbedItem))]
            
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
                regex = re.compile(r'http(s?)://.*/.*\.(png|jpg|jpeg|jpe|jfif|jif|jfi|gif|bmp|dib)', re.IGNORECASE)
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
            relevant_items = [item for item in self.contents.get_content_items() if isinstance(item, PictureItem)]
            item = relevant_items.pop(0)
            return item.image