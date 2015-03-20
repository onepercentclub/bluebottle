import json
import uuid
import mock

from django.utils import unittest
from django.test import TestCase

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.db.models import loading
from bluebottle.test.utils import BluebottleTestCase
from django.test.client import Client
from django.test.utils import override_settings

from fluent_contents.models import Placeholder
from fluent_contents.plugins.oembeditem.models import OEmbedItem
from fluent_contents.plugins.text.models import TextItem

from bluebottle.contentplugins.models import PictureItem
from bluebottle.utils.models import MetaDataModel
from bluebottle.utils.utils import clean_for_hashtag

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from ..email_backend import send_mail, create_message


BB_USER_MODEL = get_user_model()


def generate_random_slug():
    return str(uuid.uuid4())[:30]


def generate_random_email():
    return str(uuid.uuid4())[:10] + '@' + str(uuid.uuid4())[:30] + '.com'


class CustomSettingsTestCase(TestCase):

    """
    A TestCase which makes extra models available in the Django project, just
    for testing.
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
        Test that non-alphanumeric characters are excluded and proper joining
        is done
        """
        text = 'foo bar'
        self.assertEqual('FooBar', clean_for_hashtag(text))

        text = 'foo / bar /baz'
        self.assertEqual('Foo #Bar #Baz', clean_for_hashtag(text))

        text = 'foo bar /baz'
        self.assertEqual('FooBar #Baz', clean_for_hashtag(text))


class MetaTestCase(BluebottleTestCase):

    def setUp(self):
        """
        The complex work is using the fluent_contents stuff.

        Setting the 'contents' of the MetaDataModel requires setting the
        PictureItem, TextItem, OEmbedItem manually and creating a Placeholder
        to group these ContentItems on the parent.
        """

        super(MetaTestCase, self).setUp()

        # Create the MetaDataModel instance
        self.object = MetaDataModel.objects.create(
            title='Wow. Such meta. Amaze.')

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

        self.assertEqual(len(
            items), 4,
            'Error in the setUp function: not all items arecorrectly created.')

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
        # fb title falls back to default title
        self.assertEqual(item['title'], meta_data['fb_title'])

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

        # If email is set and not unique, it will raise a clearly
        # interpretable IntegrityError.
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


import mock
from django.core.exceptions import SuspiciousFileOperation


class TenantAwareStorageTest(unittest.TestCase):

    def test_location_with_tenant(self):
        """
        Test that the proper location path is generated when a tenant is
        specified
        """
        # The storage must be imported after the db connection is mocked
        with mock.patch("django.db.connection") as connection:
            from ..storage import TenantFileSystemStorage

            name = 'testname'

            connection.tenant.schema_name = 'dummy_schema_name'
            storage = TenantFileSystemStorage()

            res = storage.path(name=name)

            self.assertEqual(res.split('/')[-1], name)
            self.assertEqual(
                res.split('/')[-4:-1],
                ['static', 'media', 'dummy_schema_name'])

    def test_location_without_tenant(self):
        """
        Test that there is no tenant location path when there is no tenant
        specified
        """
        with mock.patch("django.db.connection") as connection:
            from ..storage import TenantFileSystemStorage

            name = 'testname'

            connection.tenant = None
            connection.location = "/"

            storage = TenantFileSystemStorage()

            res = storage.path(name=name)
            self.assertEqual(res.split("/")[-1], name)
            self.assertEqual(res.split("/")[-3:-1], ['static', 'media'])

    def test_raise_suspicious_error(self):
        """
        Test that a SuspiciousFileOperation is raised when the location
        path is generated
        """
        with mock.patch("django.utils._os.safe_join") as safe_join, \
                mock.patch("django.db.connection") as connection:

            from ..storage import TenantFileSystemStorage

            # Make sure that the 2nd safe_join is called in the storage code
            connection.tenant = None

            name = 'testname_join'

            safe_join.side_effect = ValueError

            storage = TenantFileSystemStorage()

            self.assertRaises(SuspiciousFileOperation, storage.path, name=name)


class SendMailTestCase(BluebottleTestCase):

    def setUp(self):
        self.user = BlueBottleUserFactory.create(email="testuser@example.com")

    @mock.patch('bluebottle.utils.email_backend.logger')
    def test_no_recipient(self, logger):
        send_mail()
        self.assertTrue(logger.error.called)
        self.assertEqual(logger.error.call_args[0][0],
                         'No recipient specified')

    @mock.patch('bluebottle.utils.email_backend.logger')
    def test_invalid_email(self, logger):
        self.user.email = 'testuser'
        self.user.save()
        send_mail(to=self.user)
        self.assertTrue(logger.error.called)
        self.assertEqual(logger.error.call_args[0][0],
                         'Trying to send email to invalid email address: {0}'.
                         format(self.user.email))

    @mock.patch('bluebottle.utils.email_backend.logger')
    def test_no_template(self, logger):
        send_mail(to=self.user)
        self.assertTrue(logger.error.called)
        self.assertEqual(logger.error.call_args[0][0],
                         'Exception while rendering email template: None.txt')

    @mock.patch('bluebottle.common.tasks._send_celery_mail')
    @override_settings(LANGUAGE_CODE='nl',
                       CELERY_MAIL=True)
    def test_celery_mail(self, celery_mail):
        send_mail(to=self.user, template_name='utils/test')
        self.assertTrue(celery_mail.delay.called)

    @mock.patch('bluebottle.utils.email_backend.create_message')
    @override_settings(LANGUAGE_CODE='nl')
    def test_no_celery_mail(self, create_message):
        send_mail(to=self.user, template_name='utils/test')
        self.assertEqual(create_message.call_count, 1)
        # Bit of a hack to check if our instance of the Mock class actually
        # does a call to .send()
        self.assertEqual(str(create_message.mock_calls[-1]),
                         'call().send()')

    @override_settings(LANGUAGE_CODE='nl')
    def test_activated_language_no_primary_language(self):
        self.user.primary_language = ''
        msg = create_message(to=self.user, template_name='utils/test')
        self.assertEqual(msg.activated_language, 'nl')

    @override_settings(LANGUAGE_CODE='nl')
    def test_activated_language_primary_language(self):
        self.user.primary_language = 'en'
        msg = create_message(to=self.user, template_name='utils/test')
        self.assertEqual(msg.activated_language, 'en')
