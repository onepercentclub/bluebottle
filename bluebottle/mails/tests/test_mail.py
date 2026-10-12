import importlib

from django.apps import apps
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.db import connection
from django.test.utils import override_settings
from django.urls import reverse

from bluebottle.mails.models import MailPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase, BluebottleTestCase

replace_email_senders = importlib.import_module(
    'bluebottle.mails.migrations.0005_sender_display_name'
).replace_email_senders


@override_settings(SEND_WELCOME_MAIL=True)
class TestMailLogo(BluebottleTestCase):
    """
    Test that email logo from backend ends up in emails
    """

    def test_mail_works_without_logo(self):
        # Upload an email logo

        BlueBottleUserFactory.create()
        email = mail.outbox[0]
        self.assertFalse('<img alt="logo"' in email.alternatives[0][0])

    def test_complete(self):
        # Upload an email logo
        with open("./bluebottle/mails/tests/images/logo-email.gif", "rb") as image_file:
            mail_settings = MailPlatformSettings.load()
            mail_settings.email_logo.save("email-logo.gif", File(image_file), save=True)
            mail_settings.save()

        BlueBottleUserFactory.create()
        email = mail.outbox[0]
        self.assertTrue('<img alt="logo"' in email.alternatives[0][0])
        self.assertTrue('http://test.localhost:3000/media/site_content/email-logo' in email.alternatives[0][0])


class MailPlatformSettingsValidationTest(BluebottleTestCase):
    def test_sender_rejects_email_address(self):
        mail_settings = MailPlatformSettings.load()
        mail_settings.sender = 'corporate.citizen.nl@goodup.com'

        with self.assertRaises(ValidationError) as error:
            mail_settings.full_clean()

        self.assertIn('sender', error.exception.error_dict)
        self.assertEqual(
            error.exception.error_dict['sender'][0].message,
            'Enter a display name, not an email address.'
        )

    def test_sender_accepts_display_name(self):
        mail_settings = MailPlatformSettings.load()
        mail_settings.sender = 'GoodUp'
        mail_settings.full_clean()


class ReplaceEmailSendersMigrationTest(BluebottleTestCase):
    def test_replaces_email_sender_with_tenant_name(self):
        mail_settings = MailPlatformSettings.load()
        mail_settings.sender = 'corporate.citizen.nl@goodup.com'
        mail_settings.save()

        replace_email_senders(apps, None)

        mail_settings.refresh_from_db()
        self.assertEqual(mail_settings.sender, connection.tenant.name)

    def test_leaves_display_name_sender_unchanged(self):
        mail_settings = MailPlatformSettings.load()
        mail_settings.sender = 'GoodUp'
        mail_settings.save()

        replace_email_senders(apps, None)

        mail_settings.refresh_from_db()
        self.assertEqual(mail_settings.sender, 'GoodUp')


class MailPlatformSettingsAdminTest(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False

    def test_sender_email_shows_validation_error(self):
        self.app.set_user(self.superuser)
        page = self.app.get(reverse('admin:mails_mailplatformsettings_change'))
        form = page.forms[1]
        form['address'] = 'info@example.com'
        form['sender'] = 'info@example.com'
        form['reply_to'] = 'replies@example.com'

        response = form.submit()

        self.assertContains(response, 'Enter a display name, not an email address.')
        mail_settings = MailPlatformSettings.load()
        self.assertNotEqual(mail_settings.sender, 'info@example.com')

    def test_sender_display_name_saves(self):
        self.app.set_user(self.superuser)
        page = self.app.get(reverse('admin:mails_mailplatformsettings_change'))
        form = page.forms[1]
        form['address'] = 'info@example.com'
        form['sender'] = 'GoodUp'
        form['reply_to'] = 'replies@example.com'

        form.submit()

        mail_settings = MailPlatformSettings.load()
        self.assertEqual(mail_settings.sender, 'GoodUp')
        self.assertEqual(mail_settings.address, 'info@example.com')
        self.assertEqual(mail_settings.reply_to, 'replies@example.com')

    def test_help_texts_are_shown(self):
        self.app.set_user(self.superuser)
        page = self.app.get(reverse('admin:mails_mailplatformsettings_change'))

        self.assertContains(page, 'Email address used as the From address for platform emails.')
        self.assertContains(
            page,
            'Name shown next to the From address, such as the platform name.'
        )
        self.assertContains(page, 'Email address used when recipients reply to a platform email.')
        self.assertContains(page, 'Optional text added at the bottom of platform emails.')
