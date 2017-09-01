from django.conf import settings
from bluebottle.test.utils import BluebottleTestCase
from django.test.utils import override_settings
from django.utils import six, translation

from bluebottle.redirects.models import Redirect


@override_settings(
    APPEND_SLASH=False,
    MIDDLEWARE_CLASSES=list(settings.MIDDLEWARE_CLASSES) + [
        'bluebottle.redirects.middleware.RedirectFallbackMiddleware'
    ],
    SITE_ID=1,
    LOCALE_REDIRECT_IGNORE=('/initial', '/news', '/project', '/external_https', '/external_http'),
)
class RedirectTests(BluebottleTestCase):
    def setUp(self):
        super(RedirectTests, self).setUp()
        self.test_url = 'http://testserver'

    def test_model(self):
        r1 = Redirect.objects.create(
            old_path='/initial', new_path='/new_target')
        self.assertEqual(six.text_type(r1), "/initial ---> /new_target")

    def test_redirect(self):
        Redirect.objects.create(
            old_path='/initial', new_path='/new_target/')
        response = self.client.get('/initial')
        self.assertRedirects(response,
                             '{0}{1}'.format(self.test_url, '/en/new_target/'),
                             status_code=301,
                             target_status_code=200)

    @override_settings(APPEND_SLASH=True)
    def test_redirect_with_append_slash(self):
        Redirect.objects.create(
            old_path='/initial/', new_path='/new_target/')
        response = self.client.get('/initial')
        self.assertRedirects(response,
                             '{0}{1}'.format(self.test_url, '/en/new_target/'),
                             status_code=301,
                             target_status_code=200)

    @override_settings(APPEND_SLASH=True)
    def test_redirect_with_append_slash_and_query_string(self):
        Redirect.objects.create(
            old_path='/initial/?foo', new_path='/new_target/')
        response = self.client.get('/initial?foo')
        self.assertRedirects(response,
                             '{0}{1}'.format(self.test_url, '/en/new_target/'),
                             status_code=301,
                             target_status_code=200)

    def test_regular_expression(self):
        Redirect.objects.create(
            old_path='/news/index/(\d+)/(.*)/',
            new_path='/my/news/$2/',
            regular_expression=True)
        response = self.client.get('/news/index/12345/foobar/')
        self.assertRedirects(response,
                             '{0}{1}'.format(self.test_url,
                                             '/en/my/news/foobar/'),
                             status_code=301, target_status_code=200)
        redirect = Redirect.objects.get(regular_expression=True)
        self.assertEqual(redirect.nr_times_visited, 1)

    def test_fallback_redirects(self):
        """
        Ensure redirects with fallback_redirect set are the last evaluated
        """
        Redirect.objects.create(
            old_path='/project/foo',
            new_path='/my/project/foo/')

        Redirect.objects.create(
            old_path='/project/foo/(.*)',
            new_path='/my/project/foo/$1/',
            regular_expression=True)

        Redirect.objects.create(
            old_path='/project/(.*)',
            new_path='/projects/',
            regular_expression=True,
            fallback_redirect=True)

        Redirect.objects.create(
            old_path='/project/bar/(.*)',
            new_path='/my/project/bar/$1/',
            regular_expression=True)

        Redirect.objects.create(
            old_path='/project/bar',
            new_path='/my/project/bar/')

        response = self.client.get('/project/foo')
        self.assertRedirects(response,
                             '{0}{1}'.format(self.test_url, '/en/my/project/foo/'),
                             status_code=301, target_status_code=200)

        response = self.client.get('/project/bar')
        self.assertRedirects(response,
                             '{0}{1}'.format(self.test_url, '/en/my/project/bar/'),
                             status_code=301, target_status_code=200)

        response = self.client.get('/project/bar/details')
        self.assertRedirects(response,
                             '{0}{1}'.format(self.test_url, '/en/my/project/bar/details/'),
                             status_code=301, target_status_code=200)

        response = self.client.get('/project/foobar')
        self.assertRedirects(response,
                             '{0}{1}'.format(self.test_url, '/en/projects/'),
                             status_code=301, target_status_code=200)

        response = self.client.get('/project/foo/details')
        self.assertRedirects(response,
                             '{0}{1}'.format(self.test_url, '/en/my/project/foo/details/'),
                             status_code=301, target_status_code=200)

    def test_redirect_external_http(self):
        Redirect.objects.create(
            old_path='/external_http', new_path='http://example.com')
        response = self.client.get('/external_http')
        # self.assertRedirects() attempts to fetch the external url, which
        # is not good in this case
        self.assertEquals(response.status_code, 301)
        self.assertEquals(response['location'], "http://example.com")

    def test_redirect_external_https(self):
        Redirect.objects.create(
            old_path='/external_https', new_path='https://example.com')
        response = self.client.get('/external_https')
        # self.assertRedirects() attempts to fetch the external url, which
        # is not good in this case
        self.assertEquals(response.status_code, 301)
        self.assertEquals(response['location'], "https://example.com")

    @override_settings(LANGUAGE_CODE='nl',
                       MIDDLEWARE_CLASSES=('bluebottle.redirects.middleware.RedirectFallbackMiddleware',))
    def test_redirect_language_code(self):
        translation.deactivate()
        Redirect.objects.create(old_path='/initial', new_path='/new_target')
        res = self.client.get('/initial')
        self.assertEqual(res.url.split('/')[3], 'nl')

    @override_settings(LANGUAGE_CODE='nl',
                       MIDDLEWARE_CLASSES=(
                           'tenant_extras.middleware.TenantLocaleMiddleware',
                           'bluebottle.redirects.middleware.RedirectFallbackMiddleware',
                       ))
    def test_redirect_with_locale_middleware(self):
        Redirect.objects.create(
            old_path='/faq', new_path='https://example.com')
        response = self.client.get('/faq')
        self.assertEquals(response.status_code, 301)
        self.assertEquals(response['location'], "https://example.com")

    @override_settings(LANGUAGE_CODE='nl',
                       MIDDLEWARE_CLASSES=(
                           'bluebottle.redirects.middleware.RedirectFallbackMiddleware',
                       ))
    def test_redirect_thread_has_language(self):
        translation.activate('en')
        Redirect.objects.create(old_path='/initial', new_path='/new_target')
        res = self.client.get('/initial')
        self.assertEqual(res.url.split('/')[3], 'en')

    @override_settings(LANGUAGE_CODE='nl',
                       LANGUAGES=(('nl', 1),),
                       MIDDLEWARE_CLASSES=(
                           'bluebottle.redirects.middleware.RedirectFallbackMiddleware',
                       ))
    def test_redirect_language_code_not_in_languages(self):
        translation.activate('en')
        Redirect.objects.create(old_path='/initial', new_path='/new_target')
        res = self.client.get('/initial')
        self.assertEqual(res.url.split('/')[3], 'nl')
