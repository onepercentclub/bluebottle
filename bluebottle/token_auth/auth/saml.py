import logging
import urlparse

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.errors import OneLogin_Saml2_Error
from onelogin.saml2.settings import OneLogin_Saml2_Settings

from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.auth.base import BaseTokenAuthentication


logger = logging.getLogger(__name__)


def get_saml_request(request):
    http_host = request.META.get('HTTP_HOST', None)
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        server_port = None
        https = request.META.get('HTTP_X_FORWARDED_PROTO') == 'https'
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

    def __init__(self, request, **kwargs):
        super(SAMLAuthentication, self).__init__(request, **kwargs)
        self.auth = OneLogin_Saml2_Auth(get_saml_request(request), self.settings)

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
            parsed = urlparse.urlparse(relay_state)

            if (
                (parsed.scheme.startswith('http') and parsed.netloc == self.request.get_host()) or
                (not parsed.scheme and not parsed.netloc and parsed.path.startswith('/'))
            ):
                return relay_state

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
        for target, source in self.settings['assertion_mapping'].items():
            try:
                data[target] = user_data[source][0]
            except KeyError:
                logger.error('Missing claim {}({})'.format(source, target))

        return data

    def authenticate_request(self):
        if 'saml_request_id' not in self.request.session:
            error = 'SAML request id missing from session'
            logger.error('Saml login error: {}'.format(error))
            raise TokenAuthenticationError(error)

        try:
            self.auth.process_response(self.request.session['saml_request_id'])
        except OneLogin_Saml2_Error, e:
            logger.error('Saml login error: {}'.format(e))
            raise TokenAuthenticationError(e)

        if self.auth.is_authenticated():
            del self.request.session['saml_request_id']
            user_data = self.auth.get_attributes()
            user_data['nameId'] = [self.auth.get_nameid()]

            return self.parse_user(user_data)
        else:
            logger.error(
                'Saml login error: {}, reason: {}, assertions: {}'.format(
                    self.auth.get_errors(), self.auth.get_last_error_reason(),
                    self.auth.get_attributes()
                )
            )

            raise TokenAuthenticationError(self.auth.get_errors())
