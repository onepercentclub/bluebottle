from builtins import object
from builtins import str
from importlib import import_module

from django.conf import settings
from django.db import connection
from django.test import TestCase, Client
from django.test.utils import override_settings
from django_webtest import WebTestMixin
from munch import munchify
from rest_framework.settings import api_settings
from rest_framework.test import APIClient as RestAPIClient
from tenant_schemas.middleware import TenantMiddleware
from tenant_schemas.utils import get_tenant_model

from bluebottle.clients import properties
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.utils import LanguageFactory
from bluebottle.utils.models import Language


def css_dict(style):
    """
    Returns a dict from a style attribute value.

    Usage::

        >>> css_dict('width: 2.2857142857142856%; overflow: hidden;')
        {'overflow': 'hidden', 'width': '2.2857142857142856%'}

        >>> css_dict('width:2.2857142857142856%;overflow:hidden')
        {'overflow': 'hidden', 'width': '2.2857142857142856%'}

    """
    if not style:
        return {}

    try:
        return dict([(k.strip(), v.strip()) for k, v in
                     [prop.split(':') for prop in
                      style.rstrip(';').split(';')]])
    except ValueError as e:
        raise ValueError('Could not parse CSS: %s (%s)' % (style, e))


class InitProjectDataMixin(object):
    def init_projects(self):
        from django.core import management

        """
        Set up some basic models needed for project creation.
        """
        management.call_command('loaddata', 'project_data.json', verbosity=0)
        management.call_command('loaddata', 'skills.json', verbosity=0)

        Language.objects.all().delete()

        language_data = [{'code': 'en', 'language_name': 'English',
                          'native_name': 'English'},
                         {'code': 'nl', 'language_name': 'Dutch',
                          'native_name': 'Nederlands'}]

        self.project_status = {}

        for language in language_data:
            LanguageFactory.create(**language)


class ApiClient(RestAPIClient):
    tm = TenantMiddleware()
    renderer_classes_list = api_settings.TEST_REQUEST_RENDERER_CLASSES
    default_format = api_settings.TEST_REQUEST_DEFAULT_FORMAT

    def __init__(self, tenant, enforce_csrf_checks=False, **defaults):
        super(ApiClient, self).__init__(enforce_csrf_checks, **defaults)

        self.tenant = tenant

        self.renderer_classes = {}
        for cls in self.renderer_classes_list:
            self.renderer_classes[cls.format] = cls

    def get(self, path, data=None, **extra):
        if 'token' in extra:
            extra['HTTP_AUTHORIZATION'] = extra['token']
            del extra['token']

        if 'HTTP_HOST' not in extra:
            extra['HTTP_HOST'] = self.tenant.domain_url

        return super(ApiClient, self).get(path, data=data, **extra)

    def post(self, path, data=None, format='json', content_type=None, **extra):
        if 'token' in extra:
            extra['HTTP_AUTHORIZATION'] = extra['token']
            del extra['token']

        if 'HTTP_HOST' not in extra:
            extra['HTTP_HOST'] = self.tenant.domain_url

        return super(ApiClient, self).post(
            path, data=data, format=format, content_type=content_type, **extra)

    def put(self, path, data=None, format='json', content_type=None, **extra):
        if 'token' in extra:
            extra['HTTP_AUTHORIZATION'] = extra['token']
            del extra['token']

        if 'HTTP_HOST' not in extra:
            extra['HTTP_HOST'] = self.tenant.domain_url

        return super(ApiClient, self).put(
            path, data=data, format=format, content_type=content_type, **extra)

    def patch(self, path, data=None, format='json', content_type=None, **extra):
        if 'token' in extra:
            extra['HTTP_AUTHORIZATION'] = extra['token']
            del extra['token']

        if 'HTTP_HOST' not in extra:
            extra['HTTP_HOST'] = self.tenant.domain_url

        return super(ApiClient, self).patch(
            path, data=data, format=format, content_type=content_type, **extra)

    def delete(self, path, data=None, format='json', content_type=None,
               **extra):
        if 'token' in extra:
            extra['HTTP_AUTHORIZATION'] = extra['token']
            del extra['token']

        if 'HTTP_HOST' not in extra:
            extra['HTTP_HOST'] = self.tenant.domain_url

        return super(ApiClient, self).delete(
            path, data=data, format=format, content_type=content_type, **extra)


@override_settings(DEBUG=True)
class BluebottleTestCase(InitProjectDataMixin, TestCase):
    def setUp(self):
        self.client = ApiClient(self.__class__.tenant)

    @classmethod
    def setUpClass(cls):
        super(BluebottleTestCase, cls).setUpClass()
        cls.tenant = get_tenant_model().objects.get(schema_name='test')
        connection.set_tenant(cls.tenant)


class BluebottleAdminTestCase(WebTestMixin, BluebottleTestCase):
    """
    Set-up webtest so we can do admin tests.
    e.g.
    payout_url = reverse('admin:payouts_projectpayout_changelist')
    response = self.app.get(payout_url, user=self.superuser)
    """

    def setUp(self):
        self.app.extra_environ['HTTP_HOST'] = str(self.tenant.domain_url)
        self.superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)

    def get_csrf_token(self, response):
        csrf = "name='csrfmiddlewaretoken' value='"
        start = response.content.decode().find(csrf) + len(csrf)
        end = response.content.decode().find("'", start)

        return response.content[start:end].decode()


class SessionTestMixin(object):
    def create_session(self):
        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        self.addCleanup(self._clear_session)

    def _clear_session(self):
        self.session.flush()


class FsmTestMixin(object):
    def pass_method(self, transaction):
        pass

    def create_status_response(self, status='AUTHORIZED', payments=None,
                               totals=None):
        if payments is None:
            payments = [{
                'id': 123456789,
                'paymentMethod': 'MASTERCARD',
                'authorization': {'status': status,
                                  'amount': {'value': 1000, '_currency': 'EUR'}}
            }]

        default_totals = {
            'totalRegistered': 1000,
            'totalShopperPending': 0,
            'totalAcquirerPending': 0,
            'totalAcquirerApproved': 0,
            'totalCaptured': 0,
            'totalRefunded': 0,
            'totalChargedback': 0
        }

        if totals is not None:
            default_totals.update(totals)

        return munchify({
            'payment': munchify(payments),
            'approximateTotals': munchify(default_totals)
        })

    def assert_status(self, instance, new_status):
        try:
            instance.refresh_from_db()
        except AttributeError:
            pass

        self.assertEqual(instance.status, new_status,
                         '{0} should change to {1} not {2}'.format(
                             instance.__class__.__name__, new_status,
                             instance.status))


class override_properties(object):
    def __init__(self, **kwargs):
        self.properties = kwargs

    def __enter__(self):
        self.old_properties = properties.tenant_properties
        properties.tenant_properties = self.properties

    def __exit__(self, *args):
        properties.tenant_properties = self.old_properties


class JSONAPITestClient(Client):

    def patch(self, path, data='',
              content_type='application/vnd.api+json',
              follow=False, secure=False, **extra):
        return super(JSONAPITestClient, self).patch(path, data, content_type, follow, secure, **extra)

    def put(self, path, data='',
            content_type='application/vnd.api+json',
            follow=False, secure=False, **extra):
        return super(JSONAPITestClient, self).put(path, data, content_type, follow, secure, **extra)

    def post(self, path, data='',
             content_type='application/vnd.api+json',
             follow=False, secure=False, **extra):
        return super(JSONAPITestClient, self).post(path, data, content_type, follow, secure, **extra)

    def generic(self, method, path, data='',
                content_type='application/vnd.api+json',
                secure=False, user=None, **extra):
        if user:
            extra['HTTP_AUTHORIZATION'] = "JWT {0}".format(user.get_jwt_token())
        return super(JSONAPITestClient, self).generic(method, path, data, content_type, secure, **extra)


def get_included(response, type):
    included = response.json()['included']
    return [include for include in included if include['type'] == type][0]
