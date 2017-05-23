import socket
import logging
from importlib import import_module
import bleach


from django.db import connection
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Permission, Group

from django_tools.middlewares import ThreadLocal
from django_fsm import TransitionNotAllowed

import pygeoip

from bluebottle.clients import properties

TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b', 'i', 'ul', 'li', 'ol', 'a',
        'br', 'pre', 'blockquote']
ATTRIBUTES = {'a': ['target', 'href']}


def clean_html(content):
    return bleach.clean(content, tags=TAGS, attributes=ATTRIBUTES)


def get_languages():
    return properties.LANGUAGES


class GetTweetMixin(object):
    def get_fb_title(self, **kwargs):
        return self.get_meta_title()

    def get_meta_title(self, **kwargs):
        if hasattr(self, 'country'):
            return u'{name_project} | {country}'.format(
                name_project=self.title,
                country=self.country.name if self.country else '')
        return self.title

    def get_tweet(self, **kwargs):
        """ Build the tweet text for the meta data """
        request = kwargs.get('request')
        if request:
            lang_code = request.LANGUAGE_CODE
        else:
            lang_code = 'en'
        twitter_handle = settings.TWITTER_HANDLES.get(
            lang_code, settings.DEFAULT_TWITTER_HANDLE)

        title = urlquote(self.get_meta_title())

        # {URL} is replaced in Ember to fill in the page url, avoiding the
        # need to provide front-end urls in our Django code.
        tweet = _(u'{title} {{URL}}').format(
            title=title, twitter_handle=twitter_handle)
        return tweet


class StatusDefinition(object):
    """
    Various status definitions for FSM's
    """
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    PENDING = 'pending'
    NEEDS_APPROVAL = 'needs_approval'
    CREATED = 'created'
    LOCKED = 'locked'
    PLEDGED = 'pledged'
    APPROVED = 'approved'
    SUCCESS = 'success'
    STARTED = 'started'
    SCHEDULED = 'scheduled'
    RE_SCHEDULED = 're_scheduled'
    CANCELLED = 'cancelled'
    AUTHORIZED = 'authorized'
    SETTLED = 'settled'
    CONFIRMED = 'confirmed'
    CHARGED_BACK = 'charged_back'
    REFUNDED = 'refunded'
    PAID = 'paid'
    FAILED = 'failed'
    RETRY = 'retry'
    PARTIAL = 'partial'
    UNKNOWN = 'unknown'


class FSMTransition(object):
    """
    Class mixin to add transition_to method for Django FSM
    """

    def transition_to(self, new_status, save=True):
        # If the new_status is the same as then current then return early
        if self.status == new_status:
            return

        # Lookup the available next transition - from Django FSM
        available_transitions = self.get_available_status_transitions()

        logging.debug("{0} (pk={1}) state changing: '{2}' to '{3}'".format(
            self.__class__.__name__, self.pk, self.status, new_status))

        # Check that the new_status is in the available transitions -
        # created with Django FSM decorator
        for transition in available_transitions:
            if transition.name == new_status:
                transition_method = transition.method

        # Call state transition method
        try:
            instance_method = getattr(self, transition_method.__name__)
            instance_method()
        except UnboundLocalError:
            raise TransitionNotAllowed(
                "Can't switch from state '{0}' to state '{1}' for {2}".format(
                    self.status, new_status, self.__class__.__name__))

        if save:
            self.save()

    def refresh_from_db(self):
        """Refreshes this instance from db"""
        new_self = self.__class__.objects.get(pk=self.pk)
        self.__dict__.update(new_self.__dict__)


def get_client_ip(request=None):
    """
    A utility method that returns the client IP for the given request.
    """
    if not request:
        request = ThreadLocal.get_current_request()

    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    except AttributeError:
        x_forwarded_for = None

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        try:
            ip = request.META.get('REMOTE_ADDR')
        except AttributeError:
            ip = None
    return ip


def set_author_editor_ip(request, obj):
    """
    A utility method to set the author, editor and IP address on an
    object based on information in a request.
    """
    if not hasattr(obj, 'author'):
        obj.author = request.user
    else:
        obj.editor = request.user
    obj.ip_address = get_client_ip(request)


def clean_for_hashtag(text):
    """
    Strip non alphanumeric charachters.

    Sometimes, text bits are made up of two parts, sepated by a slash. Split
    those into two tags. Otherwise, join the parts separated by a space.
    """
    tags = []
    bits = text.split('/')
    for bit in bits:
        # keep the alphanumeric bits and capitalize the first letter
        _bits = [_bit.title() for _bit in bit.split() if _bit.isalnum()]
        tag = "".join(_bits)
        tags.append(tag)

    return " #".join(tags)


class GetClassError(Exception):
    """ Custom exception for an GetClass """
    pass


def get_class(cl):
    # Get the class from dotted string
    try:
        # try to call handler
        parts = cl.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = import_module(module_path)
        return getattr(module, class_name)

    except (ImportError, AttributeError, ValueError) as e:
        error_message = "Could not import '%s'. %s: %s." % (cl, e.__class__.__name__, e)
        raise GetClassError(error_message)


def get_current_host():
    """
    Get the current hostname with protocol
    E.g. http://localhost:8000 or https://bluebottle.org
    """
    request = ThreadLocal.get_current_request()
    if request.is_secure():
        scheme = 'https'
    else:
        scheme = 'http'
    return '{0}://{1}'.format(scheme, request.get_host())


class InvalidIpError(Exception):
    """ Custom exception for an invalid IP address """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_country_by_ip(ip_address=None):
    """
    Returns the country associated with the IP address. Uses pygeoip
    library which is based on
    """
    if not ip_address:
        return None

    try:
        socket.inet_aton(ip_address)
    except socket.error:
        raise InvalidIpError("Invalid IP address")

    gi = pygeoip.GeoIP(settings.PROJECT_ROOT + '/GeoIP.dat')
    return gi.country_name_by_addr(ip_address)


def get_country_code_by_ip(ip_address=None):
    """
    Returns the country associated with the IP address. Uses pygeoip
    library which is based on
    the popular Maxmind's GeoIP C API
    """
    if not ip_address:
        return None

    try:
        socket.inet_aton(ip_address)
    except socket.error:
        raise InvalidIpError("Invalid IP address")

    gi = pygeoip.GeoIP(settings.PROJECT_ROOT + '/GeoIP.dat')
    return gi.country_code_by_name(ip_address)


def update_group_permissions(sender, group_perms=None):
    # Return early if there is no group permissions table. This will happen when running tests.
    if Group.objects.model._meta.db_table not in connection.introspection.table_names():
        return

    try:
        if not group_perms:
            create_permissions(sender, verbosity=False)
            try:
                group_perms = sender.module.models.GROUP_PERMS
            except AttributeError:
                return

        for group_name, permissions in group_perms.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            for perm_codename in permissions['perms']:
                permissions = Permission.objects.filter(codename=perm_codename)
                if sender:
                    permissions = permissions.filter(content_type__app_label=sender.label)
                group.permissions.add(permissions.get())

            group.save()
    except Permission.DoesNotExist, e:
        logging.debug(e)


class PreviousStatusMixin(object):
    """
    Store the status of the instance on init to be accessed as _original_status
    """
    def __init__(self, *args, **kwargs):
        super(PreviousStatusMixin, self).__init__(*args, **kwargs)

        try:
            self._original_status = self.status
        except ObjectDoesNotExist:
            self._original_status = None
