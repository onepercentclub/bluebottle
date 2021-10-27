import json
from builtins import object
from builtins import str
from contextlib import contextmanager
from importlib import import_module

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.test import TestCase, SimpleTestCase, Client
from django.test.utils import override_settings
from django_webtest import WebTestMixin
from munch import munchify
from rest_framework import status
from rest_framework.relations import RelatedField
from rest_framework.settings import api_settings
from rest_framework.test import APIClient as RestAPIClient
from tenant_schemas.middleware import TenantMiddleware
from tenant_schemas.utils import get_tenant_model
from webtest import Text

from celery.contrib.testing.worker import start_worker

from bluebottle.celery import app
from bluebottle.clients import properties
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.members.models import MemberPlatformSettings
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
        management.call_command('loaddata', 'themes.json', verbosity=0)
        management.call_command('loaddata', 'skills.json', verbosity=0)

        Language.objects.all().delete()

        language_data = [{'code': 'en', 'language_name': 'English',
                          'default': True,
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

    def included_by_type(self, response, type):
        included = response.json()['included']
        return [include for include in included if include['type'] == type]

    @classmethod
    def setUpClass(cls):
        super(BluebottleTestCase, cls).setUpClass()
        cls.tenant = get_tenant_model().objects.get(schema_name='test')
        connection.set_tenant(cls.tenant)


class APITestCase(BluebottleTestCase):
    factories = [BlueBottleUserFactory]

    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory.create()
        self.client = JSONAPITestClient()

    def perform_get(self, user=None):
        self.response = self.client.get(
            self.url,
            user=user
        )

    def perform_update(self, to_change=None, user=None):
        data = {
            'type': self.serializer.JSONAPIMeta.resource_name,
            'id': str(self.model.pk),
            'attributes': {},
            'relationships': {}
        }

        for (field, value) in to_change.items():
            if isinstance(self.serializer().get_fields()[field], RelatedField):
                data['relationships'][field] = {
                    'data': {
                        'id': value.pk,
                        'type': value.JSONAPIMeta.resource_name
                    }
                }
            else:
                data['attributes'][field] = value

        self.response = self.client.patch(
            self.url,
            json.dumps({'data': data}, cls=DjangoJSONEncoder),
            user=user
        )

        if self.response.status_code == status.HTTP_200_OK:
            self.model.refresh_from_db()

    def perform_create(self, user=None, data=None):
        if data is None:
            data = self.data

        self.response = self.client.post(
            self.url,
            json.dumps(data, cls=DjangoJSONEncoder),
            user=user
        )

        if (
            self.response.status_code == status.HTTP_201_CREATED and
            hasattr(self.serializer.Meta, 'model')
        ):
            self.model = self.serializer.Meta.model.objects.get(pk=self.response.json()['data']['id'])

    @contextmanager
    def closed_site(self):
        group = Group.objects.get(name='Anonymous')
        model_name = self.serializer.Meta.model._meta.model_name
        try:
            MemberPlatformSettings.objects.update(closed=True)
            group = Group.objects.get(name='Anonymous')
            group.permissions.remove(
                Permission.objects.get(codename='api_read_{}'.format(model_name))
            )
            yield
        finally:
            MemberPlatformSettings.objects.update(closed=False)
            group.permissions.remove(
                Permission.objects.get(codename='api_read_{}'.format(model_name))
            )

    def assertStatus(self, status):
        self.assertEqual(self.response.status_code, status)

    def assertTotal(self, count):
        if 'meta' in self.response.json():
            self.assertEqual(self.response.json()['meta']['count'], count)
        else:
            self.assertEqual(len(self.response.json()['data']), count)

    def assertIncluded(self, included, model=None):
        included_resources = [
            {'type': inc['type'], 'id': inc['id']}
            for inc in self.response.json()['included']
        ]
        relationship = self.response.json()['data']['relationships'][included]['data']

        self.assertTrue(
            {'type': relationship['type'], 'id': str(model.pk) if model else relationship['id']}
            in included_resources
        )

    def assertRelationship(self, relation, models=None):
        self.assertTrue(relation in self.response.json()['data']['relationships'])
        data = self.response.json()['data']['relationships'][relation]['data']

        if models:
            ids = [resource['id'] for resource in data]
            for model in models:
                self.assertTrue(
                    str(model.pk) in ids
                )

    def assertAttribute(self, attr, value=None):
        self.assertTrue(attr in self.response.json()['data']['attributes'])

        if value:
            self.assertEqual(getattr(self.model, attr), value)

    def assertPermission(self, permission, value):
        self.assertEqual(self.response.json()['data']['meta']['permissions'][permission], value)

    def assertTransition(self, transition):
        self.assertIn(
            transition,
            [trans['name'] for trans in self.response.json()['data']['meta']['transitions']]
        )

    def assertHasError(self, field, message):
        for error in self.response.json()['data']['meta']['errors']:
            if error['source']['pointer'] == '/data/attributes/{}'.format(field):
                if error['title'] == message:
                    return
                else:
                    self.fail(
                        '"{}" does not match the error message "{}"'.format(
                            error['title'], message
                        )
                    )
        self.fail(
            '{} does not contain an error for "{}"'.format(
                self.response.json()['data']['meta']['errors'], field
            )
        )

    def assertRequired(self, field):
        error_fields = [
            error['source']['pointer'].split('/')[-1]
            for error in self.response.json()['data']['meta']['required']
        ]
        self.assertIn(field, error_fields)

    @property
    def data(self):
        data = {
            'type': self.serializer.JSONAPIMeta.resource_name,
            'attributes': {},
            'relationships': {}
        }

        for field in self.fields:
            if field in self.defaults:
                value = self.defaults[field]
            else:
                value = getattr(self.factory, field).generate()

            if isinstance(self.serializer().get_fields()[field], RelatedField):
                serializer_name = self.serializer.included_serializers[field]
                (module, cls_name) = serializer_name.rsplit('.', 1)
                resource_name = getattr(import_module(module), cls_name).JSONAPIMeta.resource_name
                data['relationships'][field] = {
                    'data': {
                        'id': value.pk,
                        'type': resource_name
                    }
                }
            else:
                data['attributes'][field] = value

        return {'data': data}


class StateMachineTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()

    def create(self):
        return self.factory.create(**self.defaults)

    def assertTransition(self, name, user):
        error = None
        transition = None

        model = self.create()

        try:
            transition = getattr(model.states, name)
        except AttributeError:
            error = '{} has no transition "{}'.format(
                model.states, name
            )

        if transition:
            try:
                transition(user=user)
            except TransitionNotPossible as e:
                error = 'Transition "{}" not available for user {}: {}'.format(
                    name, user, e
                )

        if error:
            self.fail(error)

    def assertNoTransition(self, name, user):
        error = None
        transition = None

        model = self.create()

        try:
            transition = getattr(model.states, name)
        except AttributeError:
            error = '{} has no transition "{}'.format(
                model.states, name
            )
        if transition:
            try:
                transition(user=user)

                error = 'Transition "{}" is available for user {}, but should not be'.format(
                    name, user
                )
            except TransitionNotPossible:
                pass

        if error:
            self.fail(error)


class TriggerTestCase(BluebottleTestCase):
    def create(self):
        self.model = self.factory.create(**self.defaults)

    @contextmanager
    def execute(self, user=None):
        try:
            self.effects = self.model.execute_triggers(effects=None, user=user)
            yield self.effects
        finally:
            self.effects = None

    def _hasTransitionEffect(self, transition, model=None):
        if not model:
            model = self.model

        return TransitionEffect(transition)(model) in self.effects

    def _hasEffect(self, effect_cls, model=None):
        if not model:
            model = self.model

        for effect in self.effects:
            if effect == effect_cls(model):
                return effect

    def assertTransitionEffect(self, transition, model=None):
        if not self._hasTransitionEffect(transition, model):
            self.fail('Transition effect "{}" not triggered'.format(transition))

    def assertNoTransitionEffect(self, transition, model=None):
        if self._hasTransitionEffect(transition, model):
            self.fail('Transition effect "{}" triggered'.format(transition))

    def assertEffect(self, effect_cls, model=None):
        effect = self._hasEffect(effect_cls, model)
        if not effect:
            self.fail('Transition effect "{}" not triggered'.format(effect_cls))
        return effect

    def assertNoEffect(self, effect_cls, model=None):
        if self._hasEffect(effect_cls, model):
            self.fail('Transition effect "{}" triggered'.format(effect_cls))

    def assertNotificationEffect(self, message_cls, model=None):
        for effect in self.effects:
            if hasattr(effect, 'message') and effect.message == message_cls:
                return effect.message
        self.fail('Notification effect "{}" not triggered'.format(message_cls))


class NotificationTestCase(BluebottleTestCase):

    def create(self):
        self.message = self.message_class(self.obj)

    @property
    def _html(self):
        return BeautifulSoup(self.message.get_content_html(
            self.message.get_recipients()[0]), 'html.parser'
        )

    def assertRecipients(self, recipients):
        if recipients != self.message.get_recipients():
            self.fail("Recipients did not match: '{}' != '{}'".format(
                recipients, self.message.get_recipients())
            )

    def assertSubject(self, subject):
        if subject != self.message.generic_subject:
            self.fail("Subject did not match: '{}' != '{}'".format(
                subject, self.message.generic_subject)
            )

    def assertBodyContains(self, text):
        self.assertHtmlBodyContains(text)
        self.assertTextBodyContains(text)

    def assertTextBodyContains(self, text):
        if text not in self.text_content:
            self.fail("Text body does not contain '{}'".format(text))

    def assertHtmlBodyContains(self, text):
        if text not in self.html_content:
            self.fail("HTML body does not contain '{}'".format(text))

    @property
    def text_content(self):
        return self.message.get_content_text(self.message.get_recipients()[0])

    @property
    def html_content(self):
        return self.message.get_content_html(self.message.get_recipients()[0])

    def assertActionLink(self, url):
        link = self._html.find_all('a', {'class': 'action-email'})[0]
        if url != link['href']:
            self.fail("Action link did not match: '{}' != '{}'".format(
                url, link['href'])
            )

    def assertActionTitle(self, title):
        link = self._html.find_all('a', {'class': 'action-email'})[0]
        if title != link.string:
            self.fail("Action title did not match: '{}' != '{}'".format(
                title, link.string)
            )


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
        self.staff_member = BlueBottleUserFactory.create(is_staff=True)
        staff = Group.objects.get(name='Staff')
        staff.user_set.add(self.staff_member)
        mail.outbox = []

    def get_csrf_token(self, response):
        csrf = 'name="csrfmiddlewaretoken" value="'
        start = response.content.decode().find(csrf) + len(csrf)
        end = response.content.decode().find('"', start)
        return response.content[start:end].decode()

    def admin_add_inline_form_entry(self, form, inlines):
        fields = [field for field in form.fields.items()]
        number = form['{}-TOTAL_FORMS'.format(inlines)].value
        form['{}-TOTAL_FORMS'.format(inlines)] = int(number) + 1
        for field in fields:
            if field[0].startswith('{}-__prefix__-'.format(inlines)):
                name = field[0].replace('__prefix__', str(number))
                new = Text(form, 'input', name, None)
                form.fields[name] = [new]


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True
)
class CeleryTestCase(SimpleTestCase):
    databases = '__all__'

    factories = [BlueBottleUserFactory]

    def tearDown(self):
        for factory in self.factories:
            factory._meta.model.objects.all().delete()

    @classmethod
    def setUpClass(cls):
        from celery.contrib.testing.tasks import ping  # noqa
        print('!!!!!!!!!')

        app.conf.task_always_eager = False
        cls.celery_worker = start_worker(app)
        cls.celery_worker.__enter__()

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.celery_worker.__exit__(None, None, None)
        app.conf.task_always_eager = True
        super().tearDownClass()


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


def get_first_included_by_type(response, type):
    included = response.json()['included']
    return [include for include in included if include['type'] == type][0]
