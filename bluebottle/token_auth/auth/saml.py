import binascii

from defusedxml import DTDForbidden
from django.utils.functional import cached_property
from future import standard_library
from lxml.etree import XMLSyntaxError

from bluebottle.token_auth.models import SAMLLog

standard_library.install_aliases()
import logging
import urllib.parse

from django.utils.text import slugify

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.errors import OneLogin_Saml2_Error
from onelogin.saml2.settings import OneLogin_Saml2_Settings

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.models import Segment
from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.auth.base import BaseTokenAuthentication
from bluebottle.utils.utils import get_client_ip

logger = logging.getLogger(__name__)

GROUPS_URI = 'http://schemas.microsoft.com/ws/2008/06/identity/claims/groups'


def get_saml_request(request):
    http_host = request.headers.get('host', None)
    if 'x-forwarded-for' in request.headers:
        server_port = None
        https = request.headers.get('x-forwarded-proto') == 'https'
    else:
        server_port = request.META.get('SERVER_PORT')
        https = request.is_secure()

    saml_request = {
        'https': 'on' if https else 'off',
        'http_host': http_host,
        'script_name': request.META['PATH_INFO'],
        'get_data': request.GET.copy() or request.POST.copy(),
        'post_data': request.POST.copy()
    }

    if server_port:
        saml_request['server_port'] = server_port

    return saml_request


class SAMLAuthentication(BaseTokenAuthentication):

    def __init__(self, request, method):
        self.method = method
        super().__init__(request)

    @property
    def settings(self):
        return self.method.settings

    @cached_property
    def auth(self):
        return OneLogin_Saml2_Auth(get_saml_request(self.request), self.settings)

    def sso_url(self, target_url=None):
        result = self.auth.login(
            return_to=target_url,
            set_nameid_policy=False
        )
        self.request.session['saml_request_id'] = self.auth.get_last_request_id()

        return result

    @property
    def target_url(self):
        relay_state = self.request.POST.get('RelayState')
        if relay_state:
            parsed = urllib.parse.urlparse(relay_state)

            if (
                (parsed.scheme.startswith('http') and parsed.netloc == self.request.get_host()) or
                (((not parsed.scheme and not parsed.netloc) or parsed.scheme == 'https') and
                 parsed.path.startswith('/'))
            ):
                return parsed.path

    def get_metadata(self):
        base_path = self.settings.get('base_path', None)
        saml_settings = OneLogin_Saml2_Settings(settings=self.settings,
                                                custom_base_path=base_path,
                                                sp_validation_only=True)
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)
        if len(errors):
            logger.error('Saml configuration error: {}'.format(errors))
            raise TokenAuthenticationError(', '.join(errors))
        return metadata

    def process_logout(self):
        # Logout
        url = self.auth.process_slo()
        errors = self.auth.get_errors()
        if len(errors) == 0:
            return url

    def parse_user(self, user_data):
        data = {}
        for field in [
            'remote_id_attribute', 'email_attribute', 'first_name_attribute',
            'last_name_attribute', 'work_location_attribute'
        ]:
            source = getattr(self.method, field)
            target = field.replace('_attribute', '')
            if source in user_data:
                data[target] = user_data[source][0]
            else:
                logger.error('Missing claim {}({})'.format(source, target))

        return data

    def get_segments(self):
        segments = {}
        for segment_mapping in self.method.segment_mappings.all():
            segment_type = segment_mapping.segment_type
            try:
                value = self.attributes.get(segment_mapping.source_attribute, [])
                for val in value:
                    segment = Segment.objects.filter(
                        segment_type=segment_type
                    ).extra(
                        where=['%s ILIKE ANY (alternate_names)'],
                        params=[val, ]
                    ).first()
                    if not segment:
                        segment = Segment.objects.filter(
                            segment_type=segment_type
                        ).filter(slug=slugify(val)).first()
                    if not segment and MemberPlatformSettings.load().create_segments:
                        segment = Segment.objects.create(
                            segment_type=segment_type,
                            name=val,
                            alternate_names=[val]
                        )

                    if segment:
                        segments[segment_type.id] = segment
                        break
            except KeyError:
                logger.error(f'Missing attribute for segment {segment_type.name}')

        return segments

    def get_groups(self):
        result = []
        groups = self.attributes.get(GROUPS_URI) or []

        for group_mapping in self.method.group_mappings.all():
            if any(group_name in groups for group_name in group_mapping.group_names):
                result.append(
                    (group_mapping.group, group_mapping.staff, group_mapping.superuser)
                )

        return result

    def authenticate_request(self):
        saml_request_id = self.request.session.get(
            'saml_request_id',
            self.auth.get_last_request_id()
        )
        try:
            self.auth.process_response(saml_request_id)
            SAMLLog.log(body=self.auth.get_last_response_xml())
        except OneLogin_Saml2_Error as e:
            logger.error('Saml login error: {}'.format(e))
            raise TokenAuthenticationError(e)
        except (ValueError, binascii.Error, XMLSyntaxError, DTDForbidden) as e:
            logger.warning(
                'Rejected unreadable SAML response on %s from %s: %s: %s',
                self.request.get_host(),
                get_client_ip(self.request),
                type(e).__name__,
                e,
            )
            raise TokenAuthenticationError('Invalid SAML response')

        if self.auth.is_authenticated():
            # del self.request.session['saml_request_id']
            self.attributes = self.auth.get_attributes()
            self.attributes['nameId'] = [self.auth.get_nameid()]
            return self.parse_user(self.attributes)
        else:
            error = "Saml login error: {}, reason: {}, assertions: {}".format(
                self.auth.get_errors(),
                self.auth.get_last_error_reason(),
                self.auth.get_attributes(),
            )
            logger.error(error)

            raise TokenAuthenticationError(self.auth.get_errors())
