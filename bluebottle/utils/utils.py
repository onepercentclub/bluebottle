
from future import standard_library

standard_library.install_aliases()

from urllib.parse import urlencode

from builtins import object
import json
import logging
import socket
from collections import namedtuple
from importlib import import_module

import html2text

import bleach
import pygeoip
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Permission, Group
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import TimestampSigner
from django.core.urlresolvers import reverse
from django.db import connection
from django_fsm import TransitionNotAllowed
from django_tools.middlewares import ThreadLocal

from bluebottle.clients import properties


to_text = html2text.HTML2Text()
to_text.ignore_tables = True
to_text.ignore_images = True


TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'b', 'i', 'ul', 'li', 'ol', 'a',
        'br', 'pre', 'blockquote', 'img', 'hr', 'span', 'em', 'u']
ATTRIBUTES = {'a': ['target', 'href'], 'img': ['src', 'alt', 'width', 'height', 'align']}


def clean_html(content):
    return bleach.clean(content, tags=TAGS, attributes=ATTRIBUTES)


def get_languages():
    return properties.LANGUAGES


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
    REFUND_REQUESTED = 'refund_requested'
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
            tenant = connection.tenant.schema_name
            raise TransitionNotAllowed(
                "Can't switch from state '{0}' to state '{1}' for {2} {3} {4}".format(
                    self.status,
                    new_status,
                    self.__class__.__name__,
                    self.id,
                    tenant
                ))

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
        ipa = x_forwarded_for.split(',')[-1]
    else:
        try:
            ipa = request.META.get('REMOTE_ADDR')
        except AttributeError:
            ipa = None

    return ipa.strip() if ipa else ipa


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


def get_class(cls):
    # Get the class from dotted string
    try:
        # try to call handler
        parts = cls.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = import_module(module_path)
        return getattr(module, class_name)

    except (ImportError, AttributeError, ValueError) as err:
        error_message = "Could not import '%s'. %s: %s." % (cls, err.__class__.__name__, err)
        raise GetClassError(error_message)


def get_current_host(include_scheme=True):
    """
    Get the current hostname with protocol
    E.g. http://localhost:8000 or https://bluebottle.org
    """
    request = ThreadLocal.get_current_request()
    if request:
        host = request.get_host()
    else:
        host = connection.tenant.domain_url
    if include_scheme:
        if request and request.is_secure():
            scheme = 'https'
        else:
            scheme = 'http'
        return '{0}://{1}'.format(scheme, host)
    else:
        return host


def get_current_language():
    """
    Get the current language from request
    """
    request = ThreadLocal.get_current_request()
    if request:
        return request.LANGUAGE_CODE
    else:
        return properties.LANGUAGE_CODE


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

    gip = pygeoip.GeoIP(settings.PROJECT_ROOT + '/GeoIP.dat')
    return gip.country_name_by_addr(ip_address)


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

    gip = pygeoip.GeoIP(settings.PROJECT_ROOT + '/GeoIP.dat')
    return gip.country_code_by_name(ip_address)


def update_group_permissions(label, group_perms, apps):
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    for group_name, permissions in list(group_perms.items()):
        group, _ = Group.objects.get_or_create(name=group_name)
        for perm_codename in permissions['perms']:
            try:
                permissions = Permission.objects.filter(codename=perm_codename)
                permissions = permissions.filter(content_type__app_label=label)
                permission = permissions.last()
                if not permission:
                    raise Exception(
                        'Could not add permission: {}: Not found'.format(perm_codename)
                    )
                else:
                    group.permissions.add(permission)
            except Permission.DoesNotExist as err:
                logging.debug(err)
                raise Exception(
                    'Could not add permission: {}: {}'.format(perm_codename, err)
                )
        group.save()


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


signer = TimestampSigner()


def reverse_signed(name, args):
    url = reverse(name, args=args)
    signature = signer.sign(url)
    return '{}?{}'.format(url, urlencode({'signature': signature}))


def get_language_from_request(request):
    return request.META.get('HTTP_X_APPLICATION_LANGUAGE', None)


def _json_object_hook(d):
    return namedtuple('X', list(d.keys()))(*list(d.values()))


def json2obj(data):
    return json.loads(data, object_hook=_json_object_hook)
