import uuid
import mock
import dkim

import unittest
from django.test import TestCase

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.apps import apps
from bluebottle.test.utils import BluebottleTestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils.encoding import force_bytes
from django.conf import settings

from fluent_contents.models import Placeholder
from fluent_contents.plugins.oembeditem.models import OEmbedItem
from fluent_contents.plugins.text.models import TextItem

from moneyed import Money

from bluebottle.clients import properties
from bluebottle.contentplugins.models import PictureItem
from bluebottle.utils.models import MetaDataModel
from bluebottle.utils.utils import clean_for_hashtag
from bluebottle.utils.monkey_patch_parler import TenantAwareParlerAppsettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from ..email_backend import send_mail, create_message

from bluebottle.utils.serializers import MoneySerializer

BB_USER_MODEL = get_user_model()


def generate_random_slug():
    return str(uuid.uuid4())[:30]


def generate_random_email():
    return str(uuid.uuid4())[:10] + '@' + str(uuid.uuid4())[:30] + '.com'


def mock_attr(self, k):
    if k == 'TOKEN_AUTH':
        return {
            'assertion_mapping': {
                'email': 'email_attr',
                'first_name': 'first_name_attr',
                'last_name': 'last_name_attr'
            }
        }
    else:
        return getattr(settings, k)


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
        apps.cache.loaded = False
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
            embed_url='http://i.imgur.com/ZtRTS9h.jpg',
            parent=self.object,
            placeholder=self.ph,
            sort_order=4
        )

        # set up the client
        self.client = Client()

    def test_content_items_correctly_created(self):
        """ Test that the setUp function creates the correct items """

        items = self.object.contents.get_content_items()

        self.assertEqual(len(
            items), 4,
            'Error in the setUp function: not all items arecorrectly created.')


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


from bluebottle.utils.email_backend import TenantAwareBackend
from bluebottle.clients.mail import EmailMultiAlternatives


DKIM_PRIVATE_KEY = b"""-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDcw49R0Dy5F8mkP31iCQdgHl9TzZV8n9puQf4pYl0GnHcnj+jo
sc9s1PRMI9rxvYFdM7Vxpw9w2ryxejzWuxXPMNhn5m9Z1XNVRaxTIVEsQAYemMFM
BGVnyfELBS9QR+ewNCy7E8maIFW3CLpeMtBnGIqOjhR2zLfswkVaXQ+89QIDAQAB
AoGBAJSMluzjZWjbA9kcy77i+m6IIXcfmB5C5lVY3LB2OsiPEnKxmHSz6TJ/XV+6
pMIT1W+ksswmMPKsjVoTOcr4GqSPNMNXJFsTwSJMwso2bWLFz5stUkb9A+TLM3bV
SlGB/IoxADRbMGPnAOa/WaWwQBrBsDKwTDjp080alal5t56BAkEA931WqgtHU0Ob
k46DTgYQOdOmFE254feMcN7znwobcmanO+QiYRoONT1ZNVHM+kPE+rkhmildrCKu
nOSb/riPFQJBAORa9DAImAyD8hxMIYrzyyJv1jZjKezRzIPqsR086mkcTbYBFMS/
Nsuq2rc46a4Oy66t5uFz6XkGkJ37Cxqs7mECQH81p5Qj0/eSaqc/u3IhX7m5dkY9
ZWwmp8Nkdeirc0wsQ41fR+SNVfw7mlzzvN5ucxNEkWcCGCngccwnHZ+iEbkCQQC8
3QjW7VSsDTjh9IlNfiMEoVCe/NcA+efXNvUzhF0vf+w52p0NuEQeoHlyTkze23fU
ShoJXy+7HBXhw27EqkAhAkEAvizvS5bTzkAi7T94zWYoS0rbO/pSqzcGcNGjyisM
pk501YSTBeanQ7Y9PL17TLQjXquz0u5oqhGlRujFnt9HwA==
-----END RSA PRIVATE KEY----"""

DKIM_PUBLIC_KEY = b"""MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDcw49R0Dy
5F8mkP31iCQdgHl9TzZV8n9puQf4pYl0GnHcnj+josc9s1PRMI9rxvYFdM7Vxpw9w2ryxe
jzWuxXPMNhn5m9Z1XNVRaxTIVEsQAYemMFMBGVnyfELBS9QR+ewNCy7E8maIFW3CLpeMtB
nGIqOjhR2zLfswkVaXQ+89QIDAQAB"""


class TestTenantAwareMailServer(unittest.TestCase):
    @override_settings(
        EMAIL_BACKEND='bluebottle.utils.email_backend.DKIMBackend',
        EMAIL_HOST='somehost',
        EMAIL_PORT=1337)
    @mock.patch("smtplib.SMTP")
    def test_settings_config(self, smtp):
        """ Test simple / traditional case where config comes from settings """
        be = TenantAwareBackend()
        msg = EmailMultiAlternatives(subject="test", body="test",
                                     to=["test@example.com"])

        # open the connection explicitly so we can get the
        # connection reference. It will be cleared once closed
        # in send_messages
        be.open()
        connection = be.connection

        be.send_messages([msg])

        self.assertTrue(smtp.called)
        self.assertEquals(smtp.call_args[0], ('somehost', 1337))
        self.assertTrue(connection.sendmail.called)

    @override_settings(
        EMAIL_BACKEND='bluebottle.utils.email_backend.DKIMBackend',
        EMAIL_HOST='somehost',
        EMAIL_PORT=1337)
    @mock.patch("smtplib.SMTP")
    def test_tenant_dkim_settings(self, smtp):
        """ test setup where tenant config differs from global settings """

        with mock.patch("bluebottle.utils.email_backend.properties",
                        new=mock.Mock([])) as properties:
            properties.MAIL_CONFIG = {'HOST': 'tenanthost', 'PORT': 4242}

            properties.DKIM_SELECTOR = "key2"
            properties.DKIM_DOMAIN = "testserver"
            properties.DKIM_PRIVATE_KEY = DKIM_PRIVATE_KEY

            be = TenantAwareBackend()
            msg = EmailMultiAlternatives(subject="test", body="test",
                                         to=["test@example.com"])

            be.open()
            connection = be.connection
            be.send_messages([msg])

            to_bytes = lambda s: force_bytes(s, 'utf-8')

            def _plain_key(s):
                return b"".join([l for l in s.split(b'\n') if not l.startswith(b'---')])

            signed_msg = connection.sendmail.call_args[0][2]
            dkim_message = dkim.DKIM(message=to_bytes(signed_msg))
            dkim_check = dkim_message.verify(dnsfunc=lambda name: b"".join([b"v=DKIM1; p=", _plain_key(DKIM_PUBLIC_KEY)]))

            self.assertTrue(signed_msg.find("d=testserver") >= 0)
            self.assertTrue(signed_msg.find("s=key2") >= 0)
            self.assertTrue(dkim_check, "Email should be signed by tenant")


    @override_settings(
        EMAIL_BACKEND='bluebottle.utils.email_backend.DKIMBackend',
        EMAIL_HOST='somehost',
        EMAIL_PORT=1337)
    @mock.patch("smtplib.SMTP")
    def test_tenant_config(self, smtp):
        """ test setup where tenant config differs from global settings """

        with mock.patch("bluebottle.utils.email_backend.properties",
                        new=mock.Mock([])) as properties:
            properties.MAIL_CONFIG = {'HOST': 'tenanthost', 'PORT': 4242}

            be = TenantAwareBackend()
            msg = EmailMultiAlternatives(subject="test", body="test",
                                         to=["test@example.com"])

            # open the connection explicitly so we can get the
            # connection reference. It will be cleared once closed
            # in send_messages
            be.open()
            connection = be.connection

            be.send_messages([msg])

            self.assertTrue(smtp.called)
            self.assertEquals(smtp.call_args[0], ('tenanthost', 4242))
            self.assertTrue(connection.sendmail.called)


class MoneySerializerTestCase(BluebottleTestCase):
    def setUp(self):
        self.serializer = MoneySerializer()

    def test_amount_to_money(self):
        data = 10

        self.assertEqual(
            self.serializer.to_internal_value(data),
            Money(10, 'EUR')
        )

    def test_float_to_money(self):
        data = 10.0

        self.assertEqual(
            self.serializer.to_internal_value(data),
            Money(10.0, 'EUR')
        )

    def test_object_to_money(self):
        data = {'amount': 10, 'currency': 'USD'}

        self.assertEqual(
            self.serializer.to_internal_value(data),
            Money(10, 'USD')
        )


class TestTenantAwareParlerAppsettings(BluebottleTestCase):
    def setUp(self):
        super(TestTenantAwareParlerAppsettings, self).setUp()
        self.appsettings = TenantAwareParlerAppsettings()
        languages = (
            ('nl', 'Dutch'),
            ('en', 'English'),
        )

        setattr(properties, 'LANGUAGES', languages)

    def test_language_code(self):
        self.assertEqual(self.appsettings.PARLER_DEFAULT_LANGUAGE_CODE, 'en')

    def test_languages(self):
        parler_languages = self.appsettings.PARLER_LANGUAGES
        self.assertEqual(parler_languages['default']['code'], 'en')
        self.assertEqual(parler_languages[1][0]['code'], 'nl')
        self.assertEqual(parler_languages[1][1]['code'], 'en')

    def test_default(self):
        self.assertEqual(self.appsettings.PARLER_SHOW_EXCLUDED_LANGUAGE_TABS, False)
        pass
