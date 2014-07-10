from selenium import webdriver
import time
import urlparse
import os
import sys

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import LiveServerTestCase
from django.test.utils import override_settings

from splinter.browser import _DRIVERS
from splinter.element_list import ElementList
from splinter.exceptions import DriverNotFoundError

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


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


RUN_LOCAL = os.environ.get('RUN_TESTS_LOCAL') == 'False'

if RUN_LOCAL:
    # could add Chrome, PhantomJS etc... here
    browsers = ['Firefox']
else:
    from sauceclient import SauceClient
    USERNAME = os.environ.get('SAUCE_USERNAME')
    ACCESS_KEY = os.environ.get('SAUCE_ACCESS_KEY')
    sauce = SauceClient(USERNAME, ACCESS_KEY)


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
            caps = {'platform': 'Linux', 'browserName': 'firefox', 'version': '30'}

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

            cls.browser = BrowserExt(driver_name='remote', url=url, browser='firefox',
                                     wait_time=10, desired_capabilities=caps)
            cls.browser.driver.implicitly_wait(5)
        else:
            cls.browser = BrowserExt(settings.SELENIUM_WEBDRIVER, wait_time=10)

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

    def login(self, username, password):
        """
        Perform login operation on the website.

        :param username: The user's email address.
        :param password: The user's password
        :return: ``True`` if login was successful.
        """
        self.visit_homepage()

        # Find the link to the signup button page and click it.
        self.browser.find_link_by_itext('log in').first.click()

        # Validate that we are on the intended page.
        if not self.browser.is_text_present('LOG IN', wait_time=10):
            return False

        # Fill in details.
        self.browser.fill('username', username)
        self.browser.fill('password', password)

        self.browser.find_by_value('Login').first.click()

        return self.browser.is_text_present('PROFILE', wait_time=10)

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

        # # Check if the homepage opened, and the dynamically loaded content appeared.
        # # Remember that
        return self.browser.is_text_present('2013 Bluebottle', wait_time=10)

    def assertDatePicked(self):
        # Pick a deadline next month
        self.assertTrue(self.scroll_to_and_click_by_css(".hasDatepicker"))

        # Wait for date picker popup
        self.assertTrue(self.browser.is_element_present_by_css("#ui-datepicker-div"))

        # Click Next to get a date in the future
        self.browser.find_by_css("[title=Next]").first.click()
        self.assertTrue(self.browser.is_text_present("10"))
        self.browser.find_link_by_text("10").first.click()

    def scroll_to_by_css(self, selector):
        element = self.wait_for_element_css(selector)

        if element:
            y = int(element.location['y']) - 100
            x = int(element.location['x'])
            self.browser.execute_script("window.scrollTo(%s,%s)" % (x, y))

        return element

    def scroll_to_and_click_by_css(self, selector):
        element = self.scroll_to_by_css(selector);
        
        if element:
            element.click()
            return True
        else:
            return False

    def scroll_to_and_fill_by_css(self, selector, text):
        element = self.scroll_to_by_css(selector);

        if element:
            element.send_keys(text)
            return True
        else:
            return False
            
    def wait_for_element_css(self, selector, timeout=10):
        wait = WebDriverWait(self.browser.driver, timeout)
        try:
            element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))

            return element
        except TimeoutException:
            return None

    def is_visible(self, selector, timeout=10):
        return not self.wait_for_element_css(selector, timeout) is None

    def assert_css(self, selector, wait_time=10):
        return self.assertTrue(self.browser.is_element_present_by_css(selector, wait_time=wait_time) )

    def assert_text(self, text, wait_time=10):
        return self.assertTrue(self.browser.is_text_present(text, wait_time=wait_time) )
