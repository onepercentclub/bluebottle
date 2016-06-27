# -*- coding: utf-8 -*-
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.common.tasks import _send_celery_mail
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import get_country_by_ip, InvalidIpError


class TestUtilsTestCase(BluebottleTestCase):
    def test_no_ip(self):
        self.assertEqual(get_country_by_ip(), None)

    def test_invalid_ip(self):
        with self.assertRaises(InvalidIpError):
            get_country_by_ip("123abc")

    def test_valid_ip(self):
        self.assertEqual(get_country_by_ip("213.127.165.114"), "Netherlands")


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
