from decimal import Decimal

import mock
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from rest_framework import status

from bluebottle.analytics.models import AnalyticsPlatformSettings, AnalyticsAdapter
from bluebottle.clients import properties
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.funding_flutterwave.tests.factories import FlutterwavePaymentProviderFactory
from bluebottle.funding_stripe.tests.factories import StripePaymentProviderFactory
from bluebottle.funding_vitepay.tests.factories import VitepayPaymentProviderFactory
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.projects.models import ProjectPlatformSettings, ProjectSearchFilter
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

    def test_settings_currencies(self):
        StripePaymentProviderFactory.create()
        FlutterwavePaymentProviderFactory.create()
        VitepayPaymentProviderFactory.create()

        # Check that exposed property is in settings api, and other settings are not shown
        response = self.client.get(self.settings_url)

        self.assertEqual(
            response.data['currencies'],
            [
                {
                    'minAmount': 5,
                    'symbol': u'CFA',
                    'code': 'XOF',
                    'name': u'West African CFA Franc',
                    'rate': Decimal('1000.000000')
                },
                {
                    'minAmount': 5,
                    'symbol': u'\u20a6',
                    'code': 'NGN',
                    'name': u'Nigerian Naira',
                    'rate': Decimal('500.000000')
                },
                {
                    'minAmount': 5,
                    'symbol': u'$',
                    'code': 'USD',
                    'name': u'US Dollar',
                    'rate': Decimal('1.000000')
                },
                {
                    'minAmount': 5,
                    'symbol': 'KES',
                    'code': 'KES',
                    'name': u'Kenyan Shilling',
                    'rate': Decimal('100.000000')
                },
                {
                    'minAmount': 5,
                    'symbol': u'\u20ac',
                    'code': 'EUR',
                    'name': u'Euro',
                    'rate': Decimal('1.500000')
                }
            ]
        )


class TestDefaultAPI(BluebottleTestCase):
    """
    Test the default API, open and closed, authenticated or not
    with default permissions
    """
    def setUp(self):
        super(TestDefaultAPI, self).setUp()

        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        self.projects_url = reverse('project_list')

    def test_open_api(self):
        """ request open api, expect projects """
        response = self.client.get(self.projects_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch('bluebottle.clients.properties.CLOSED_SITE', True)
    def test_closed_api_not_authenticated(self):
        """ request closed api, expect 403 ? if not authenticated """
        anonymous = Group.objects.get(name='Anonymous')
        anonymous.permissions.remove(
            Permission.objects.get(codename='api_read_project')
        )

        response = self.client.get(self.projects_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_closed_api_authenticated(self):
        """ request closed api, expect projects if authenticated """
        response = self.client.get(self.projects_url, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestPlatformSettingsApi(BluebottleTestCase):
    """
    Test platform settings api.
    """

    def setUp(self):
        super(TestPlatformSettingsApi, self).setUp()
        self.init_projects()
        self.settings_url = reverse('settings')

    def test_project_platform_settings(self):
        # Create some project settings and confirm they end up correctly in settings api
        project_settings = ProjectPlatformSettings.objects.create(
            create_types=['sourcing', 'funding'],
            contact_types=['organization'],
            create_flow='choice',
            contact_method='email'
        )
        ProjectSearchFilter.objects.create(
            project_settings=project_settings,
            name='location'
        )
        ProjectSearchFilter.objects.create(
            project_settings=project_settings,
            name='theme'
        )
        ProjectSearchFilter.objects.create(
            project_settings=project_settings,
            name='status',
            default='campaign,voting'
        )
        ProjectSearchFilter.objects.create(
            project_settings=project_settings,
            name='type',
            values='volunteering,funding'
        )
        filters = [
            {'name': 'location', 'default': None, 'values': None, 'sequence': 1},
            {'name': 'theme', 'default': None, 'values': None, 'sequence': 2},
            {'name': 'status', 'default': 'campaign,voting', 'values': None, 'sequence': 3},
            {'name': 'type', 'default': None, 'values': 'volunteering,funding', 'sequence': 4},
        ]

        response = self.client.get(self.settings_url)
        self.assertEqual(
            set(response.data['platform']['projects']['create_types']),
            set(['funding', 'sourcing'])
        )
        self.assertEqual(response.data['platform']['projects']['contact_types'], ['organization'])
        self.assertEqual(response.data['platform']['projects']['contact_method'], 'email')
        self.assertEqual(response.data['platform']['projects']['filters'], filters)

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
            require_organization=True
        )

        response = self.client.get(self.settings_url)

        self.assertEqual(response.data['platform']['initiatives']['activity_types'], ['event', 'job'])
        self.assertEqual(response.data['platform']['initiatives']['require_organization'], True)

    def test_analytics_platform_settings(self):
        # Create analytics platform settings and confirm they end up correctly in settings api
        analytics_settings = AnalyticsPlatformSettings.objects.create()
        AnalyticsAdapter.objects.create(
            analytics_settings=analytics_settings,
            type='SiteCatalyst',
            code='AB-345-GG'
        )

        data = {
            'type': 'SiteCatalyst',
            'code': 'AB-345-GG'
        }
        response = self.client.get(self.settings_url)
        self.assertEqual(response.data['platform']['analytics']['adapters'][0], data)

    @override_settings(
        PAYOUT_METHODS=[{
            'currencies': [u'EUR'],
            'method': u'rabobank',
            'payment_methods': [u'docdata-creditcard', u'docdata-ideal', u'docdata-directdebit']
        }, {
            'currencies': [u'EUR', 'USD'],
            'method': u'stripe',
            'payment_methods': [u'stripe-creditcard', u'stripe-ideal', u'stripe-directdebit']
        }, {
            'currencies': [u'EUR'],
            'method': u'excel',
            'payment_methods': [u'pledge-standard']
        }]
    )
    def test_payout_settings(self):
        response = self.client.get(self.settings_url)
        data = response.data['platform']['payouts']

        self.assertEqual(set(data['EUR']), set(['rabobank', 'excel', 'stripe']))
        self.assertEqual(set(data['USD']), set(['stripe']))
