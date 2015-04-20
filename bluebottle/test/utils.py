import time
import urlparse
import os
import json
import requests
import base64

from bunch import bunchify

from django.db import connection
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import LiveServerTestCase
from django.test.utils import override_settings
from django.test import TestCase

from rest_framework.settings import api_settings
from rest_framework.test import APIClient as RestAPIClient

from tenant_schemas.middleware import TenantMiddleware
from tenant_schemas.utils import get_tenant_model

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
        return dict([(k.strip(), v.strip()) for k, v in [prop.split(':') for prop in style.rstrip(';').split(';')]])
    except ValueError, e:
        raise ValueError('Could not parse CSS: %s (%s)' % (style, e))


class InitProjectDataMixin(object):

    def init_projects(self):
        from django.core import management
        """
        Set up some basic models needed for project creation.
        """
        management.call_command('loaddata', 'project_data.json', verbosity=0)

        Language.objects.all().delete()

        language_data = [{'code': 'en', 'language_name': 'English', 'native_name': 'English'},
                         {'code': 'nl', 'language_name': 'Dutch', 'native_name': 'Nederlands'}]

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

    def create_status_response(self, status='AUTHORIZED', payments=None, totals=None):
        if payments is None:
            payments = [{
                'id': 123456789,
                'paymentMethod': 'MASTERCARD',
                'authorization': {'status': status, 'amount': {'value': 1000, '_currency': 'EUR'}}
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

        return bunchify({
            'payment': bunchify(payments),
            'approximateTotals': bunchify(default_totals)
        })

    def assert_status(self, instance, new_status):
        try:
            instance.refresh_from_db()
        except AttributeError:
            pass

        self.assertEqual(instance.status, new_status,
            '{0} should change to {1} not {2}'.format(instance.__class__.__name__, new_status, instance.status))
