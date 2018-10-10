from bluebottle.common.models import CommonPlatformSettings
from django.test.client import RequestFactory

from bluebottle.auth.middleware import LockdownMiddleware
from bluebottle.test.utils import BluebottleTestCase
from django.test.utils import override_settings


class LockdownTestCase(BluebottleTestCase):
    def setUp(self):
        super(LockdownTestCase, self).setUp()

    def test_lockdown_page(self):
        common_settings = CommonPlatformSettings.load()
        common_settings.lockdown = True
        common_settings.save()
        mw = LockdownMiddleware()
        rf = RequestFactory()
        request = rf.get('/')
        request.session = type("MockSession", (object, ), {"get": lambda self, prop: "bla"})()
        response = mw.process_request(request)
        self.assertEqual(response.status_code, 401)

    def test_lockdown_access_page(self):
        common_settings = CommonPlatformSettings.load()
        common_settings.lockdown = True
        common_settings.lockdown_password = 'pssssst'
        common_settings.save()
        mw = LockdownMiddleware()
        rf = RequestFactory()
        request = rf.get('/')
        request.META = {'HTTP_X_LOCKDOWN_TOKEN': common_settings.token}
        request.session = type("MockSession", (object, ), {"get": lambda self, prop: "bla"})()
        response = mw.process_request(request)
        self.assertIsNone(response)

    @override_settings(
        FORCE_LOCKDOWN=True,
        LOCKDOWN_PASSWORD='pssssst'
    )
    def test_force_lockdown(self):
        common_settings = CommonPlatformSettings.load()
        common_settings.lockdown = False
        common_settings.lockdown_password = 'overridden'
        common_settings.save()
        mw = LockdownMiddleware()
        rf = RequestFactory()
        request = rf.get('/')
        request.session = type("MockSession", (object, ), {"get": lambda self, prop: "bla"})()
        response = mw.process_request(request)
        self.assertEqual(response.status_code, 401)

    def test_no_lockdown_page(self):
        common_settings = CommonPlatformSettings.load()
        common_settings.lockdown = False
        common_settings.save()
        mw = LockdownMiddleware()
        rf = RequestFactory()
        request = rf.get('/')
        request.session = type("MockSession", (object, ), {"get": lambda self, prop: "bla"})()
        response = mw.process_request(request)
        self.assertIsNone(response)
