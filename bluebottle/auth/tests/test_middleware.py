from django.test.client import RequestFactory

from bluebottle.auth.middleware import LockdownMiddleware
from bluebottle.test.utils import BluebottleTestCase


class LockdownTestCase(BluebottleTestCase):
    def setUp(self):
        super(LockdownTestCase, self).setUp()

    def test_lockdown_page(self):
        mw = LockdownMiddleware()
        rf = RequestFactory()
        request = rf.get('/')
        request.META = {'HTTP_X_LOCKDOWN': 'sssht'}
        # Mock a session
        request.session = type("MockSession", (object, ), {"get": lambda self, prop: "bla"})()
        response = mw.process_request(request)
        self.assertEqual(response.status_code, 401)
        self.assertTrue('<style>' in response.content)
