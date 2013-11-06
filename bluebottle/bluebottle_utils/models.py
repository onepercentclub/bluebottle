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
    from fluent_contents.plugins.picture.models import PictureItem
    from fluent_contents.plugins.text.models import TextItem
    from fluent_contents.rendering import render_placeholder
    from sorl.thumbnail import ImageField
    from taggit_autocomplete_modified.managers import TaggableManagerAutocomplete as TaggableManager


    class MetaDataModel(models.Model):
        """
        This is a model purely for MetaData testing in the API.
        """
        title = models.CharField(max_length=50)
        tags = TaggableManager(blank=True)
        contents = PlaceholderField("blog_contents")