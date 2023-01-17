from decimal import Decimal

import mock
from django.contrib.auth.models import Group, Permission
from django.test.utils import override_settings
from django.urls import reverse
from django_elasticsearch_dsl.test import ESTestCase
from rest_framework import status

from bluebottle.clients import properties
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.funding.models import FundingPlatformSettings
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.notifications.models import NotificationPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class ClientSettingsTestCase(BluebottleTestCase):

    def setUp(self):
        super(ClientSettingsTestCase, self).setUp()
        self.settings_url = reverse('settings')

    @override_settings(PARENT={'child': True}, EXPOSED_TENANT_PROPERTIES=['parent.child'])
    def test_nested_exposed_properties(self):
        response = self.client.get(self.settings_url)
        self.assertEqual(response.data['parent']['child'], True)

    @override_settings(CLOSED_SITE=False, TOP_SECRET="*****", EXPOSED_TENANT_PROPERTIES=['closed_site'])
    def test_settings_show(self):
        # Check that exposed property is in settings api, and other settings are not shown
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['closedSite'], False)
        self.assertNotIn('topSecret', response.data)

        # Check that exposed setting gets overwritten by client property
        setattr(properties, 'CLOSED_SITE', True)
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['closedSite'], True)

        # Check that previously hidden setting can be exposed
        setattr(properties, 'EXPOSED_TENANT_PROPERTIES', ['closed_site', 'top_secret'])
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('topSecret', response.data)

        setattr(properties, 'CLOSED_SITE', False)

    @override_settings(TOKEN_AUTH={'assertion_mapping': {'first_name': 'urn:first_name'}})
    def test_settings_read_only(self):
        # Check that exposed property is in settings api, and other settings are not shown
        response = self.client.get(self.settings_url)
        self.assertEqual(response.data['readOnlyFields'], {'user': ['first_name']})

    @override_settings(
        PAYMENT_METHODS=[{
            'provider': 'docdata',
            'id': 'docdata-ideal',
            'profile': 'ideal',
            'name': 'iDEAL',
            'restricted_countries': ('NL',),
            'currencies': {
                'EUR': {'max_amount': 100}
            }
        }, {
            'provider': 'docdata',
            'id': 'docdata-directdebit',
            'profile': 'directdebit',
            'name': 'Direct Debit',
            'restricted_countries': ('NL', 'BE',),
            'currencies': {
                'EUR': {'min_amount': 10, 'max_amount': 100}
            }

        }, {
            'provider': 'docdata',
            'id': 'docdata-creditcard',
            'profile': 'creditcard',
            'name': 'CreditCard',
            'currencies': {
                'USD': {'min_amount': 5, 'max_amount': 100},
                'NGN': {'min_amount': 3000, 'max_amount': 100},
                'XOF': {'min_amount': 5000, 'max_amount': 100},
            }
        }],
        DEFAULT_CURRENCY='USD'
    )
    def test_settings_currencies(self):
        # Check that exposed property is in settings api, and other settings are not shown
        response = self.client.get(self.settings_url)
        expected = [
            {
                'symbol': '€',
                'code': 'EUR',
                'name': 'Euro',
                'rate': Decimal(1.5),
                'minAmount': 0
            },
            {
                'symbol': '₦',
                'code': 'NGN',
                'name': 'Nigerian Naira',
                'rate': Decimal(500.0),
                'minAmount': 3000
            },
            {
                'symbol': '$',
                'code': 'USD',
                'name': 'US Dollar',
                'rate': Decimal(1.0),
                'minAmount': 5
            },
            {
                'symbol': 'CFA',
                'code': 'XOF',
                'name': 'West African CFA Franc',
                'rate': Decimal(1000.0),
                'minAmount': 5000
            },
        ]
        result = response.data['currencies']
        result = sorted(result, key=lambda i: i['name'])
        expected = sorted(expected, key=lambda i: i['name'])
        self.assertEqual(result, expected)


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
class TestDefaultAPI(ESTestCase, BluebottleTestCase):
    """
    Test the default API, open and closed, authenticated or not
    with default permissions
    """

    def setUp(self):
        super(TestDefaultAPI, self).setUp()

        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        self.initiatives_url = reverse('initiative-list')

    def test_open_api(self):
        """ request open api, expect projects """
        response = self.client.get(self.initiatives_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch('bluebottle.clients.properties.CLOSED_SITE', True)
    def test_closed_api_not_authenticated(self):
        """ request closed api, expect 403 ? if not authenticated """
        anonymous = Group.objects.get(name='Anonymous')
        anonymous.permissions.remove(
            Permission.objects.get(codename='api_read_initiative')
        )

        response = self.client.get(self.initiatives_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_closed_api_authenticated(self):
        """ request closed api, expect projects if authenticated """
        response = self.client.get(self.initiatives_url, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestPlatformSettingsApi(BluebottleTestCase):
    """
    Test platform settings api.
    """

    def setUp(self):
        super(TestPlatformSettingsApi, self).setUp()
        self.init_projects()
        self.settings_url = reverse('settings')

    def test_site_platform_settings(self):
        # Create site platform settings and confirm they end up correctly in settings api
        SitePlatformSettings.objects.create(
            contact_email='malle@epp.ie',
            contact_phone='+3163202128',
            copyright='Malle Eppie Ltd.',
            powered_by_text='Powered by',
            powered_by_link='https://epp.ie'
        )
        response = self.client.get(self.settings_url)
        self.assertEqual(response.data['platform']['content']['contact_email'], 'malle@epp.ie')
        self.assertEqual(response.data['platform']['content']['contact_phone'], '+3163202128')
        self.assertEqual(response.data['platform']['content']['copyright'], 'Malle Eppie Ltd.')
        self.assertEqual(response.data['platform']['content']['powered_by_link'], 'https://epp.ie')
        self.assertEqual(response.data['platform']['content']['powered_by_text'], 'Powered by')

    def test_initiative_platform_settings(self):
        # Create initiative platform settings and confirm they end up correctly in settings api
        InitiativePlatformSettings.objects.create(
            activity_types=['event', 'job'],
            initiative_search_filters=['category', 'location'],
            activity_search_filters=['type', 'skill', 'status'],
            contact_method='phone',
            require_organization=True,
            team_activities=True
        )

        response = self.client.get(self.settings_url)
        self.assertEqual(response.data['platform']['initiatives']['activity_types'], ['event', 'job'])
        self.assertEqual(
            response.data['platform']['initiatives']['activity_search_filters'],
            ['type', 'skill', 'status']
        )
        self.assertEqual(
            response.data['platform']['initiatives']['initiative_search_filters'],
            ['category', 'location']
        )
        self.assertEqual(response.data['platform']['initiatives']['require_organization'], True)
        self.assertEqual(response.data['platform']['initiatives']['contact_method'], 'phone')
        self.assertEqual(response.data['platform']['initiatives']['team_activities'], True)

    def test_notification_platform_settings(self):
        # Create notification platform settings and confirm they end up correctly in settings api
        NotificationPlatformSettings.objects.create(
            match_options=True,
            share_options=['twitter', 'facebook_at_work'],
            default_yammer_group_id='1234',
            facebook_at_work_url='https://my.facebook.com'
        )

        response = self.client.get(self.settings_url)
        self.assertEqual(response.data['platform']['notifications']['match_options'], True)
        self.assertEqual(response.data['platform']['notifications']['share_options'], ['twitter', 'facebook_at_work'])
        self.assertEqual(response.data['platform']['notifications']['facebook_at_work_url'], 'https://my.facebook.com')
        self.assertEqual(response.data['platform']['notifications']['default_yammer_group_id'], '1234')

    def test_funding_platform_settings(self):
        # Create funding platform settings and confirm they end up correctly in settings api
        FundingPlatformSettings.objects.create(
            allow_anonymous_rewards=True
        )

        response = self.client.get(self.settings_url)
        self.assertEqual(response.data['platform']['funding']['allow_anonymous_rewards'], True)

    def test_member_platform_settings(self):
        MemberPlatformSettings.objects.create(
            closed=False,
            require_consent=True,
            retention_anonymize=24,
            retention_delete=36
        )

        response = self.client.get(self.settings_url)
        self.assertEqual(response.data['platform']['members']['closed'], False)
        self.assertEqual(response.data['platform']['members']['require_consent'], True)
        self.assertEqual(response.data['platform']['members']['retention_anonymize'], 24)
        self.assertEqual(response.data['platform']['members']['retention_delete'], 36)

    def test_member_platform_settings_closed(self):
        MemberPlatformSettings.objects.create(
            closed=True,
            require_consent=True,
        )

        user = BlueBottleUserFactory.create()
        user_token = "JWT {0}".format(user.get_jwt_token())

        response = self.client.get(self.settings_url, token=user_token)
        self.assertEqual(response.data['platform']['members']['closed'], True)
        self.assertEqual(response.data['platform']['members']['require_consent'], True)

    def test_member_platform_settings_closed_anonymous(self):
        MemberPlatformSettings.objects.create(
            closed=True,
            require_consent=True,
        )

        response = self.client.get(self.settings_url)

        content = {
            'contact_email': None,
            'contact_phone': None,
            'copyright': None,
            'powered_by_link': None,
            'powered_by_logo': None,
            'powered_by_text': None,
            'metadata_title': None,
            'metadata_description': None,
            'metadata_keywords': None,
            'start_page': None,
            'logo': None,
            'favicons': {
                'large': '',
                'small': ''
            },
            'action_color': None,
            'action_text_color': '#ffffff',
            'alternative_link_color': None,
            'description_color': None,
            'description_text_color': '#ffffff',
            'footer_color': '#3b3b3b',
            'footer_text_color': '#ffffff',
            'title_font': None,
            'body_font': None
        }
        members = {
            'closed': True,
            'background': '',
            'login_methods': ['password'],
            'session_only': False,
            'email_domain': None,
            'confirm_signup': False
        }

        self.assertEqual(response.data['platform']['members'], members)
        self.assertEqual(response.data['platform']['content'], content)

    def test_member_platform_required_settings(self):
        MemberPlatformSettings.objects.create(
            require_office=True,
            verify_office=False
        )

        response = self.client.get(self.settings_url)
        self.assertEqual(response.data['platform']['members']['require_office'], True)
        self.assertEqual(response.data['platform']['members']['verify_office'], False)
