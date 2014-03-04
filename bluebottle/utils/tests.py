import json
import uuid
import unittest

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.db.models import loading
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from fluent_contents.models import Placeholder
from fluent_contents.plugins.oembeditem.models import OEmbedItem
from fluent_contents.plugins.text.models import TextItem

from bluebottle.contentplugins.models import PictureItem
from .models import MetaDataModel
from .utils import clean_for_hashtag


BB_USER_MODEL = get_user_model()


def generate_random_slug():
    return str(uuid.uuid4())[:30]


def generate_random_email():
    return str(uuid.uuid4())[:10] + '@' + str(uuid.uuid4())[:30] + '.com'


class CustomSettingsTestCase(TestCase):
    """
    A TestCase which makes extra models available in the Django project, just for testing.
    Based on http://djangosnippets.org/snippets/1011/ in Django 1.4 style.
    """
    new_settings = {}
    _override = None

    @classmethod
    def setUpClass(cls):
        cls._override = override_settings(**cls.new_settings)
        cls._override.enable()
        if 'INSTALLED_APPS' in cls.new_settings:
            cls.syncdb()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        if 'INSTALLED_APPS' in cls.new_settings:
            cls.syncdb()

    @classmethod
    def syncdb(cls):
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)


class HashTagTestCase(unittest.TestCase):
    def test_clean_text_for_hashtag(self):
        """
        Test that non-alphanumeric characters are excluded and proper joining is done
        """
        text = 'foo bar'
        self.assertEqual('FooBar', clean_for_hashtag(text))

        text = 'foo / bar /baz'
        self.assertEqual('Foo #Bar #Baz', clean_for_hashtag(text))

        text = 'foo bar /baz'
        self.assertEqual('FooBar #Baz', clean_for_hashtag(text))


class MetaTestCase(TestCase):
    def setUp(self):
        """
        The complex work is using the fluent_contents stuff.

        Setting the 'contents' of the MetaDataModel requires setting the
        PictureItem, TextItem, OEmbedItem manually and creating a Placeholder to
        group these ContentItems on the parent.
        """

        # Create the MetaDataModel instance
        self.object = MetaDataModel.objects.create(title='Wow. Such meta. Amaze.')

        # Add in a placeholder
        self.ph = Placeholder.objects.create(
            parent=self.object,
            title='Foo',
            slot='blog_contents'
        )

        """ Time to create some content items... """
        # Simple text item
        self.text_item = TextItem.objects.create(
            text='<p>I am doge</p>',
            parent=self.object,
            placeholder=self.ph,
            sort_order=1
        )

        # Don't bother simulating uploads, that's not the scope of this test
        self.picture = PictureItem.objects.create(
            image='images/kitten_snow.jpg',
            parent=self.object,
            placeholder=self.ph,
            sort_order=2,
        )

        # OEmbed object, with youtube link
        self.youtube = OEmbedItem.objects.create(
            embed_url='http://www.youtube.com/watch?v=0ETxuM-hq8c',
            parent=self.object,
            placeholder=self.ph,
            sort_order=3
        )

        # Imgur
        self.imgur = OEmbedItem.objects.create(
            embed_url='http://imgur.com/gallery/CXLgSVc',
            parent=self.object,
            placeholder=self.ph,
            sort_order=4
        )

        # Add tags...
        tags = ['Tag 1', 'Tag 2']
        self.object.tags.add(*tags)

        # set up the client
        self.client = Client()
        self.url = reverse('meta_test', kwargs={'pk': self.object.id})

    def test_content_items_correctly_created(self):
        """ Test that the setUp function creates the correct items """

        items = self.object.contents.get_content_items()

        self.assertEqual(len(items), 4, 'Error in the setUp function: not all items are correctly created.')

    def test_return_metadata(self):
        """
        Verify that the MetaField functions work and can correctly retrieve
        the desired meta data.
        """

        # get the metadata through the API
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        item = json.loads(response.content)
        meta_data = item.get('meta_data')

        # verify that indeed the title is the same and attribute lookups are ok
        self.assertEqual(item['title'], meta_data['title'])
        self.assertEqual(item['title'], meta_data['fb_title']) # fb title falls back to default title

        # verify that callables work
        img1 = 'images/kitten_snow.jpg'
        # FIXME!
        # self.assertIn(img1, meta_data['image'])

    def test_image_source(self):
        """ Image source can return an image to be serialized, or an url """

        # get the metadata through the API
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        item = json.loads(response.content)
        meta_data = item.get('meta_data2')

        # this image has to be processed by sorl.thumbnail
        # the filename differs (hash or something similar), and 'cache'
        # should be in the url

        # FIXME!
        # self.assertNotEqual(meta_data['image'], self.picture.image.url)
        # self.assertIn('cache', meta_data['image'])

    def test_url_tag_in_tweet(self):
        """
        Test that {URL} is present by default in tweets, to be replaced by
        Ember
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        item = json.loads(response.content)
        meta_data = item.get('meta_data')

        self.assertIn('{URL}', meta_data['tweet'])

class UserTestsMixin(object):
    """ Mixin base class for tests requiring users. """

    def create_user(self, email=None, password=None, **extra_fields):
        """ Create, save and return a new user. """

        # If email is set and not unique, it will raise a clearly interpretable IntegrityError.
        # If auto-generated, make sure it's unique.
        if not email:
            email = generate_random_email()
            while BB_USER_MODEL.objects.filter(email=email).exists():
                email = generate_random_email()

        user = BB_USER_MODEL.objects.create_user(email=email, **extra_fields)

        if not password:
            user.set_password('password')

        user.save()

        return user
