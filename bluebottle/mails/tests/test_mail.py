from django.core import mail
from django.core.files.base import File
from django.test.utils import override_settings

from bluebottle.mails.models import MailPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


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
        image_file = open("./bluebottle/mails/tests/images/logo-email.gif", "rb")
        mail_settings = MailPlatformSettings.load()
        mail_settings.email_logo.save("email-logo.gif", File(image_file), save=True)
        mail_settings.save()
        BlueBottleUserFactory.create()
        email = mail.outbox[0]
        self.assertTrue('<img alt="logo"' in email.alternatives[0][0])
