from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from bluebottle.bluebottle_drf2.middleware import (
    METHOD_OVERRIDE_HEADER,
    MethodOverrideMiddleware,
)


def dummy_view(request):
    return HttpResponse(request.method)


class MethodOverrideMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = MethodOverrideMiddleware(dummy_view)

    def _run_view(self, request):
        self.middleware.process_view(request, dummy_view, (), {})
        return dummy_view(request)

    def test_post_with_override_header_changes_method(self):
        request = self.factory.post(
            '/api/test',
            HTTP_X_HTTP_METHOD_OVERRIDE='PATCH',
        )
        response = self._run_view(request)
        self.assertEqual(response.content.decode(), 'PATCH')

    def test_get_request_is_unchanged(self):
        request = self.factory.get('/api/test')
        response = self._run_view(request)
        self.assertEqual(response.content.decode(), 'GET')

    def test_post_without_override_stays_post(self):
        request = self.factory.post('/api/test')
        response = self._run_view(request)
        self.assertEqual(response.content.decode(), 'POST')

    def test_override_header_constant(self):
        self.assertEqual(METHOD_OVERRIDE_HEADER, 'HTTP_X_HTTP_METHOD_OVERRIDE')
