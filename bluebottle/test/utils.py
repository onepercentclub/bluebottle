import time
import urlparse
import os
import sys
import json
import requests
import base64

from bunch import bunchify

import django
from django.db import connection
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import LiveServerTestCase
from django.test.utils import override_settings
from django.test import TestCase
from django.core.management import call_command

from rest_framework.compat import force_bytes_or_smart_bytes
from rest_framework.settings import api_settings
from rest_framework.test import APIClient as RestAPIClient

from tenant_schemas.test.cases import TenantTestCase
from tenant_schemas.middleware import TenantMiddleware
from tenant_schemas.test.client import TenantClient
from tenant_schemas.utils import get_public_schema_name, get_tenant_model

from bluebottle.test.factory_models.projects import ProjectPhaseFactory, ProjectThemeFactory
from bluebottle.bb_projects.models import ProjectPhase, ProjectTheme
from bluebottle.test.factory_models.utils import LanguageFactory
from bluebottle.utils.models import Language
from bluebottle.clients.models import Client


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
        return dict([(k.strip(), v.strip()) for k, v in [prop.split(':') for prop in style.rstrip(';').split(';')]])
    except ValueError, e:
        raise ValueError('Could not parse CSS: %s (%s)' % (style, e))


class InitProjectDataMixin(object):

    def init_projects(self):
        """
        Set up some basic models needed for project creation.
        """
        Language.objects.all().delete()

        language_data = [{'code': 'en', 'language_name': 'English', 'native_name': 'English'},
                         {'code': 'nl', 'language_name': 'Dutch', 'native_name': 'Nederlands'}]

        self.project_status = {}

        for language in language_data:
            LanguageFactory.create(**language)
            

RUN_LOCAL = os.environ.get('RUN_TESTS_LOCAL') == 'False'

if RUN_LOCAL:
    # could add Chrome, PhantomJS etc... here
    browsers = ['Firefox']
else:
    from sauceclient import SauceClient
    USERNAME = os.environ.get('SAUCE_USERNAME')
    ACCESS_KEY = os.environ.get('SAUCE_ACCESS_KEY')
    sauce = SauceClient(USERNAME, ACCESS_KEY)


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
        if extra.has_key('token'):
            extra['HTTP_AUTHORIZATION'] = extra['token']
            del extra['token']

        if 'HTTP_HOST' not in extra:
            extra['HTTP_HOST'] = self.tenant.domain_url

        return super(ApiClient, self).get(path, data=data, **extra)

    def post(self, path, data=None, format='json', content_type=None, **extra):
        if extra.has_key('token'):
            extra['HTTP_AUTHORIZATION'] = extra['token']
            del extra['token']

        if 'HTTP_HOST' not in extra:
            extra['HTTP_HOST'] = self.tenant.domain_url

        return super(ApiClient, self).post(
            path, data=data, format=format, content_type=content_type, **extra)

    def put(self, path, data=None, format='json', content_type=None, **extra):
        if extra.has_key('token'):
            extra['HTTP_AUTHORIZATION'] = extra['token']
            del extra['token']

        if 'HTTP_HOST' not in extra:
            extra['HTTP_HOST'] = self.tenant.domain_url
 
        return super(ApiClient, self).put(
            path, data=data, format=format, content_type=content_type, **extra)

    def patch(self, path, data=None, format='json', content_type=None, **extra):
        if extra.has_key('token'):
            extra['HTTP_AUTHORIZATION'] = extra['token']
            del extra['token']

        if 'HTTP_HOST' not in extra:
            extra['HTTP_HOST'] = self.tenant.domain_url
                
        return super(ApiClient, self).patch(
            path, data=data, format=format, content_type=content_type, **extra)

    def delete(self, path, data=None, format='json', content_type=None, **extra):
        if extra.has_key('token'):
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
        # create a tenant
        tenant_domain = 'testserver'
        cls.tenant = get_tenant_model()(
            domain_url=tenant_domain, 
            schema_name='test',
            client_name='test')

        cls.tenant.save(verbosity=0)  # todo: is there any way to get the verbosity from the test command here?
        connection.set_tenant(cls.tenant)

    @classmethod
    def tearDownClass(cls):
        # delete tenant
        connection.set_schema_to_public()
        cls.tenant.delete()

        cursor = connection.cursor()
        cursor.execute('DROP SCHEMA test CASCADE')


class FsmTestMixin(object):
    def pass_method(self, transaction):
        pass

    def create_status_response(self, status='AUTHORIZED'):
        return bunchify({
            'payment': [{
                'id': 123456789,
                'amount': 1000,
                'authorization': {'status': status}}
            ],
            'approximateTotals': {
                'totalRegistered': 1000,
                'totalShopperPending': 0,
                'totalAcquirerPending': 0,
                'totalAcquirerApproved': 0,
                'totalCaptured': 0,
                'totalRefunded': 0,
                'totalChargedback': 0
            }
        })

    def assert_status(self, instance, new_status):
        try:
            instance.refresh_from_db()
        except AttributeError:
            pass

        self.assertEqual(instance.status, new_status,
            '{0} should change to {1} not {2}'.format(instance.__class__.__name__, new_status, instance.status))
