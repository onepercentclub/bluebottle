# -*- coding: utf-8 -*-
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.common.tasks import _send_celery_mail
from bluebottle.test.utils import BluebottleTestCase


class TestCeleryMail(BluebottleTestCase):
    def test_no_unicode_encode_error(self):
        """ Test handling a unicode character in subject or body """
        s = u'\u2019'
        msg = EmailMultiAlternatives(subject=s,
                                     body=s,
                                     to=['test@testing.com'])
        try:
            _send_celery_mail(msg)
        except UnicodeEncodeError:
            self.fail("Unicode string not handled correctly")

    def test_handle_non_unicode_char(self):
        """ Test handling a non-unicode character in subject or body """
        s = '€'
        msg = EmailMultiAlternatives(subject=s,
                                     body=s,
                                     to=['test@testing.com'])
        _send_celery_mail(msg)


class TestFacebookWallpost(BluebottleTestCase):
    pass
