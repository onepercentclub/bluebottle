import json
import mock
import time
from urlparse import urlparse, parse_qs

from django.test.utils import override_settings

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.looker.utils import LookerSSOEmbed
from bluebottle.test.utils import BluebottleTestCase


@mock.patch(
    'bluebottle.looker.utils.get_current_host',
    return_value='goodup.com'
)
@override_settings(LOOKER_SECRET='123456')
class LookerEmbedDashboardTest(BluebottleTestCase):
    """
    Test main admin dashboard
    """

    def setUp(self):
        super(LookerEmbedDashboardTest, self).setUp()
        self.user = BlueBottleUserFactory.create(
            first_name='Test',
            last_name='De Tester'
        )

    def test_url(self, get_current_host):
        embed = LookerSSOEmbed(self.user, 'look', '1')
        url = urlparse(embed.url)
        query = parse_qs(url.query)

        self.assertEqual(url.scheme, 'https')
        self.assertEqual(
            url.netloc, 'looker.{}'.format(get_current_host.return_value)
        )
        self.assertEqual(
            query['first_name'][0], json.dumps(self.user.first_name)
        )
        self.assertEqual(
            query['last_name'][0], json.dumps(self.user.last_name)
        )
        self.assertEqual(
            query['external_user_id'][0],
            json.dumps('test-{}'.format(self.user.pk))
        )
        self.assertTrue(
            query['nonce'][0].startswith('"') and query['nonce'][0].endswith('"')
        )
        self.assertTrue(
            int(query['time'][0]) - int(time.time()) < 2
        )
        self.assertEqual(
            len(query['signature'][0]), 28
        )
        self.assertEqual(
            json.loads(query['user_attributes'][0])['tenant'], 'test'
        )
        self.assertEqual(
            int(query['session_length'][0]), LookerSSOEmbed.session_length
        )
        self.assertEqual(
            json.loads(query['permissions'][0]), list(LookerSSOEmbed.permissions)
        )
        self.assertEqual(
            json.loads(query['models'][0]), list(LookerSSOEmbed.models)
        )

    @override_settings(LOOKER_HOST='looker.example.com')
    def test_host_in_settings(self, get_current_host):
        embed = LookerSSOEmbed(self.user, 'look', 1)
        url = urlparse(embed.url)

        self.assertEqual(url.scheme, 'https')
        self.assertEqual(
            url.netloc, 'looker.example.com'
        )
