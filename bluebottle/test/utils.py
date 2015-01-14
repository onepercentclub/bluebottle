from selenium import webdriver
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

from splinter.browser import _DRIVERS
from splinter.element_list import ElementList
from splinter.exceptions import DriverNotFoundError

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

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


def BrowserExt(driver_name='firefox', url=None, wait_time=5, browser='firefox', desired_capabilities={}, *args, **kwargs):
    """
    Small helper to combine the correct webdriver with some additional methods without cloning the project.
    """
    try:
        driver_class = _DRIVERS[driver_name]
    except KeyError:
        raise DriverNotFoundError("No driver for %s" % driver_name)

    class DriverClassExt(driver_class):
        """
        This class is an extension that overrides certain functions to allow custom behaviour.
        """
        def visit(self, url):
            """
            Visit and wait for redirect. Also performs the redirect.
            """
            super(DriverClassExt, self).visit(url)
            
            if self.driver_name == 'PhantomJS':
                time.sleep(3) # Allow the page to load correctly.

                if self.status_code.code in [302, 301]:
                    loc = self.response.msg['Location']
                    redirect_url = urlparse.urlparse(loc)
                    parsed_url = urlparse.urlparse(self.request_url)
            
                    # Build new absolute URL.
                    absolute_url = urlparse.urlunparse([
                            redirect_url.scheme,
                            redirect_url.netloc,
                            redirect_url.path,
                            redirect_url.params,
                            redirect_url.query,
                            parsed_url.fragment
                            ])
                    self.visit(absolute_url)

    new_class = type('BrowserExt', (DriverClassExt, WebDriverAdditionMixin), {})

    if driver_name == 'PhantomJS':
        kwargs.update({'load_images': False})

    if driver_name=='remote':
        return new_class(url=url, browser=browser, wait_time=wait_time, **desired_capabilities)

    return new_class(*args, **kwargs)


class WebDriverAdditionMixin(object):
    """
    Additional helper methods for the web driver.
    """
    def fill_form_by_css(self, form, data):
        """
        Fills in a form by finding input elements by CSS.

        :param form: The form ``WebElement``.
        :param data: A dict in the form ``{'input css': 'value'}``.
        """

        if not isinstance(data, dict):
            raise RuntimeError('Argument data must be dict.')

        # Fill in the form.
        for css, val in data.items():
            form.find_by_css(css).first.fill(val)

    def fill_form_by_label(self, form, data):
        """
        Fills in a form by finding labels.

        NOTE: This function works best if you define all labels and input elements in your data.

        :param form: The form ``WebElement``.
        :param data: List of tuples in the form ``[('label', 'value'), ...]``. The value can also be a list if multiple
                     inputs are connected to a single label.

        Example::

            # ...
            self.fill_form_by_label(
                self.browser.find_by_tag('form'),
                [
                    ('Name', ['John', 'Doe']),
                    ('Email', 'johndoe@onepercentclub.com'),
                ]
            )

        """
        if not isinstance(data, list):
            raise RuntimeError('Argument data must be a list of tuples.')

        labels = form.find_by_tag('label')
        inputs = form.find_by_css('input, textarea, select')

        # Fill in the form. Keep an offset for if multiple inputs are used.
        offset = 0
        for label_text, values in data:
            if not isinstance(values, list):
                values = [values]

            for index, form_label in enumerate(labels):
                if form_label.text.strip('\r\n ') == label_text:
                    for i, val in enumerate(values):
                        offset += i

                        if val is None:
                            continue

                        form_input = inputs[index + offset]
                        form_input_tag_name = form_input.tag_name

                        if form_input_tag_name == 'input':
                            form_input_type = form_input['type']

                            if form_input_type == 'file':
                                #form_input.attach_file(val)
                                self.attach_file(form_input['name'], val)
                            elif form_input_type == 'checkbox':
                                if val:
                                    form_input.check()
                                else:
                                    form_input.uncheck()
                            elif form_input_type == 'radio':
                                radio_group = form_input['name']
                                self.choose(radio_group, val)
                            else:
                                form_input.fill(val)
                        elif form_input_tag_name == 'select':
                            # Workaround for form_input.select(val) which uses the name attribute to find the options.
                            # However, some select elements do not have a name attribute.
                            # TODO: Report issue found in Splinter 0.5.3
                            for option in form_input.find_by_tag('option'):
                                if option['value'] == val:
                                    option.click()
                                    break
                        else:
                            form_input.fill(val)
                    break

    def find_link_by_itext(self, text, exact=False):
        """
        Finds a link by text in a more robust way than the default method. Also allows for case sensitive and
        insensitive matches.

        :param text: The text to search for within a link element.
        :param exact: ``True`` if the match mut be an exact match. ``False`` (default) for case insensitive matches.

        :return: List of matching elements.
        """
        result = []
        for link in self.find_by_css('a, button, input[type="button"], input[type="submit"]'):
            if link.text == text or (not exact and link.text.lower() == text.lower()):
                result.append(link)
        return ElementList(result, find_by='link by itext', query=text)


class InitProjectDataMixin(object):

    def init_projects(self):
        """
        Set up some basic models needed for project creation.
        """
        ProjectPhase.objects.all().delete()
        ProjectTheme.objects.all().delete()
        Language.objects.all().delete()

        phase_data = [{'sequence': 1, 'name': 'Plan - New', 'viewable': False},
                      {'sequence': 2, 'name': 'Plan - Submitted', 'viewable': False},
                      {'sequence': 3, 'name': 'Plan - Needs Work', 'viewable': False},
                      {'sequence': 4, 'name': 'Plan - Rejected', 'viewable': False},
                      {'sequence': 6, 'name': 'Plan - Accepted', 'viewable': True},
                      {'sequence': 5, 'name': 'Campaign', 'viewable': True},
                      {'sequence': 7, 'name': 'Stopped', 'viewable': False},
                      {'sequence': 8, 'name': 'Realised', 'viewable': True},
                      {'sequence': 9, 'name': 'Done - Incomplete', 'viewable': True},
                      {'sequence': 10, 'name': 'Done - Complete', 'viewable': True}]

        theme_data = [{'name': 'Education'},
                      {'name': 'Environment'},
                      {'name': 'Health'}]

        language_data = [{'code': 'en', 'language_name': 'English', 'native_name': 'English'},
                         {'code': 'nl', 'language_name': 'Dutch', 'native_name': 'Nederlands'}]

        self.project_status = {}

        for phase in phase_data:
            status = ProjectPhaseFactory.create(**phase)
            self.project_status[status.slug] = status

        for theme in theme_data:
            ProjectThemeFactory.create(**theme)

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



@override_settings(DEBUG=True)
class SeleniumTestCase(LiveServerTestCase):
    """
    Selenium test cases should inherit from this class.

    Wrapper around ``LiveServerTestCase`` to provide a standard browser instance. In addition it performs some tests to
    make sure all settings are correct.
    """

    @classmethod
    def setUpClass(cls):
        """
        Prepare the test class rather then doing this for every individual test.
        """
        if not hasattr(settings, 'SELENIUM_WEBDRIVER'):
            raise ImproperlyConfigured('Define SELENIUM_WEBDRIVER in your settings.py.')

        if settings.SELENIUM_WEBDRIVER == 'remote':

            name = 'Manual test run'
            caps = {'platform': 'Linux', 'browserName': 'chrome', 'version': '35'}

            if 'TRAVIS_BUILD_NUMBER' in os.environ:
                name = 'Build ' + os.environ['TRAVIS_BUILD_NUMBER']
                if 'TRAVIS_PULL_REQUEST' in os.environ:
                    name = 'Pull Request #' + os.environ['TRAVIS_PULL_REQUEST']
                caps['name'] = name
                caps['tunnel-identifier'] = os.environ['TRAVIS_JOB_NUMBER']
                caps['build'] = os.environ['TRAVIS_BUILD_NUMBER']
                caps['tags'] = ['Travis', 'CI']

            username = os.environ.get('SAUCE_USERNAME')
            access_key = os.environ.get('SAUCE_ACCESS_KEY')
            sauce_url = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"
            url = sauce_url % (username, access_key)

            cls.browser = BrowserExt(driver_name='remote', url=url, browser='chrome',
                                     wait_time=30, desired_capabilities=caps)
        else:
            cls.browser = BrowserExt(settings.SELENIUM_WEBDRIVER, wait_time=30)

        cls.browser.driver.implicitly_wait(2)
        cls.browser.driver.set_page_load_timeout(30)

        super(SeleniumTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(SeleniumTestCase, cls).tearDownClass()

    def _post_teardown(self):
        """
        Allow PhantomJS to close down properly after a test. It can still perform requests after the last test statement
        was made. 
        """
        time.sleep(3)

        super(SeleniumTestCase, self)._post_teardown()

    def login(self, username, password, wait_time=30):
        """
        Perform login operation on the website.

        :param username: The user's email address.
        :param password: The user's password
        :return: ``True`` if login was successful.
        """
        self.visit_homepage()

        if not self.browser.find_by_css('.nav-signup-login'):
            self.logout()

        # Find the link to the signup button page and click it.
        self.scroll_to_and_click_by_css('.nav-signup-login a')
        self.wait_for_element_css('input[name=username]')

        # Fill in details.
        self.browser.find_by_css('input[name=username]').first.fill(username)
        self.browser.find_by_css('input[type=password]').first.fill(password)

        self.wait_for_element_css("a[name=login]", timeout=wait_time)
        self.scroll_to_and_click_by_css("a[name=login]")

        # Wait for modal animation to complete
        self.wait_for_not_element_css('.modal-fullscreen-background')

        return self.wait_for_element_css(".nav-member", timeout=wait_time)

    def logout(self):
        self.visit_path("/logout")
        return self.wait_for_element_css('.nav-signup-login')

    def visit_path(self, path, lang_code=None):
        """
        Visits a relative path of the website.

        :param path: The relative URL path.
        :param lang_code: A two letter language code as used in the URL.
        """
        if lang_code is None:
            lang_code = 'en'

        if path and not path.startswith('#!'):
            path = '#!%s' % path

        # Open the homepage (always the starting point), in English.
        return self.browser.visit('%(url)s/%(lang_code)s/%(path)s' % {
            'url': self.live_server_url,
            'lang_code': lang_code,
            'path': path
        })        

    def visit_homepage(self, lang_code=None):
        """
        Convenience function to open the homepage.

        :param lang_code: A two letter language code as used in the URL.
        :return: ``True`` if the homepage could be visited.
        """
        
        self.visit_path('', lang_code)

        # Check if the homepage opened, and the dynamically loaded content appeared.
        return self.browser.is_text_present('2013 Bluebottle', wait_time=10)

    def assertDatePicked(self):
        # Focus input to make the date picker popup open
        self.scroll_to_by_css(".hasDatepicker").send_keys(Keys.NULL)

        # Wait for date picker popup
        self.assertTrue(self.browser.is_element_present_by_css("#ui-datepicker-div"))

        # Click Next to get a date in the future
        self.assert_css('[title=Next]')
        
        # store the current month
        thisMonth = int(self.browser.find_by_css('.ui-datepicker-month option[selected]').value)
        
        # Click through to the next month
        self.scroll_to_and_click_by_css('[title=Next]')

        # Wait until the new month loads - 0 == January
        nextMonth = (0 if thisMonth == 11 else thisMonth+1)
        self.assert_css('.ui-datepicker-month option[value="{0}"][selected]'.format(nextMonth))

        # Select the 10th day
        self.browser.find_link_by_text("10").first.click()

    def scroll_to_by_css(self, selector):
        element = self.wait_for_element_css(selector)

        if element:
            y = int(element.location['y']) - 100
            x = int(element.location['x'])
            self.browser.execute_script("window.scrollTo(%s,%s)" % (x, y))

        return element

    def scroll_to_and_click_by_css(self, selector):
        element = self.scroll_to_by_css(selector)

        if element:
            element.click()
            return True
        else:
            return False

    def scroll_to_and_fill_by_css(self, selector, text):
        element = self.scroll_to_by_css(selector)

        if element:
            element.send_keys(text)
            return True
        else:
            return False
            
    # This function isn't very useful when the element is fading in with JS/CSS.
    # It is probably better to use the assert_css function below which also takes a timeout but
    # will not assert true until the element is fully visible, eg opacity is also 1.
    def wait_for_element_css(self, selector, timeout=30):
        wait = WebDriverWait(self.browser.driver, timeout)
        try:
            element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
            return element
        except TimeoutException:
            return None

    def wait_for_n_elements_css(self, selector, n, timeout=30):
        wait = WebDriverWait(self.browser.driver, timeout)
        try:
            wait.until(lambda s: len(s.find_elements(By.CSS_SELECTOR, selector)) == n)
            return self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
        except TimeoutException:
            return None

    def wait_for_element_css_index(self, selector, index=0, timeout=30):
        wait = WebDriverWait(self.browser.driver, timeout)
        try:
            wait.until(lambda s: len(s.find_elements(By.CSS_SELECTOR, selector)) > index)
            return self.browser.driver.find_elements(By.CSS_SELECTOR, selector)[index]
        except TimeoutException:
            return None

    def wait_for_not_element_css(self, selector, timeout=5):
        """
        Wait for an element with this css to disappear.
        """
        wait = WebDriverWait(self.browser.driver, timeout)
        try:
            wait.until(lambda s: len(s.find_elements(By.CSS_SELECTOR, selector)) == 0)
        except TimeoutException:
            return None

    def wait_for_toast_to_disappear(self):
        # Wait until the toast message disappears.
        return self.wait_for_not_element_css('.flash.is-active', 10)

    def wait_for_modal_to_disappear(self):
        # Wait until the toast message disappears.
        return self.wait_for_not_element_css('.modal-fullscreen-background', 10)

    def close_modal(self):
        # Close modal, if any
        self.browser.find_by_css('body').type(Keys.ESCAPE)

    def is_visible(self, selector, timeout=10):
        return not self.wait_for_element_css(selector, timeout) is None

    def assert_css(self, selector, wait_time=10):
        return self.assertTrue(self.browser.is_element_present_by_css(selector, wait_time=wait_time) )

    def assert_text(self, text, wait_time=10):
        return self.assertTrue(self.browser.is_text_present(text, wait_time=wait_time) )

    def upload_screenshot(self):
        client_id = os.environ.get('IMGUR_CLIENT_ID')
        client_key = os.environ.get('IMGUR_CLIENT_SECRET')

        if client_id and client_key:
            client_auth = 'Client-ID {0}'.format(client_id)
            headers = {'Authorization': client_auth}
            url = 'https://api.imgur.com/3/upload.json'
            filename = '/tmp/screenshot.png'

            print 'Attempting to save screenshot...'
            self.browser.driver.save_screenshot(filename)

            response = requests.post(
                url,
                headers = headers,
                data = {
                    'key': client_key,
                    'image': base64.b64encode(open(filename, 'rb').read()),
                    'type': 'base64',
                    'name': filename,
                    'title': 'Travis Screenshot'
                }
            )

            print 'Uploaded screenshot:'
            data = json.loads(response.content)
            print data['data']['link']
            print response.content

        else:
            print 'Imgur API keys not found!'

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
