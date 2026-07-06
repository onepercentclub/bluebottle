import re

from bluebottle.members.models import MemberPlatformSettings
import django_otp


from django.conf import settings
from django.contrib.auth import login
from django.core.exceptions import ImproperlyConfigured
from django.http.response import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from rest_framework.exceptions import PermissionDenied
from django.template import loader
from django.views.generic.base import View, TemplateView

from bluebottle.clients import properties
from bluebottle.members.sso import get_configured_sso_providers, get_sso_provider
from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.auth.saml import SAMLAuthentication
from bluebottle.token_auth.models import SAMLDevice
from bluebottle.utils.utils import get_client_ip


SSO_PROVIDER_SESSION_KEY = 'sso_provider_id'


def get_auth(request, settings, saml_request=None):
    return SAMLAuthentication(request, settings, saml_request=saml_request)


def get_saml_settings_for_redirect(request):
    provider_id = request.GET.get('provider')
    providers = get_configured_sso_providers()

    if provider_id:
        provider = get_sso_provider(provider_id)
        request.session[SSO_PROVIDER_SESSION_KEY] = str(provider.pk)
        return provider.to_token_auth_settings()

    if len(providers) == 1:
        request.session[SSO_PROVIDER_SESSION_KEY] = str(providers[0].pk)
        return providers[0].to_token_auth_settings()

    if len(providers) > 1:
        return None

    try:
        return properties.TOKEN_AUTH
    except AttributeError:
        return None


def get_saml_settings_for_request(request):
    provider_id = request.GET.get('provider') or request.session.get(SSO_PROVIDER_SESSION_KEY)
    if provider_id:
        try:
            provider = get_sso_provider(provider_id)
            if provider:
                return provider.to_token_auth_settings()
        except ImproperlyConfigured:
            pass

    providers = get_configured_sso_providers()
    if len(providers) == 1:
        return providers[0].to_token_auth_settings()

    try:
        return properties.TOKEN_AUTH
    except AttributeError:
        raise ImproperlyConfigured('Missing SSO configuration')


class TokenRedirectView(View):
    """
    Redirect to SSO login page
    """
    permanent = False
    query_string = True

    def get(self, request, *args, **kwargs):
        client_ip = get_client_ip(request)

        if client_ip == settings.VPN_CLIENT_IP or client_ip == '127.0.0.1':
            saml_settings = settings.SUPPORT_TOKEN_AUTH
        else:
            saml_settings = get_saml_settings_for_redirect(request)
            if not saml_settings:
                return HttpResponseRedirect('/token/error?message=SSO+provider+required')

        auth = get_auth(request, settings=saml_settings, **kwargs)
        sso_url = auth.sso_url(target_url=request.build_absolute_uri(request.GET.get('url')))
        return HttpResponseRedirect(sso_url)


class SAMLLoginView(View):
    def get_auth(self, request):
        return get_auth(request, self.settings)

    def authenticated(self, user, auth, created):
        pass

    def post(self, request):
        auth = self.get_auth(request)

        try:
            user, created = auth.authenticate()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
        except TokenAuthenticationError as e:
            url = '/token/error?message={0}'.format(e)
            return HttpResponseRedirect(url)

        try:
            self.authenticated(user, auth, created)
        except PermissionDenied as e:
            return HttpResponseForbidden(str(e))

        target_url = auth.target_url or "/"

        if target_url and re.match('^\/\w\w\/admin', target_url):
            # Admin login:
            # Log user in using cookies and redirect directly
            login(request, user)

            (device, _created) = SAMLDevice.objects.get_or_create(user=user)
            django_otp.login(request, device)

            return HttpResponseRedirect(target_url)

        template = loader.get_template('utils/login_with.html')
        context = {'token': user.get_jwt_token(), 'link': target_url}
        response = HttpResponse(template.render(context, request), content_type='text/html')
        response['cache-control'] = "no-store, no-cache, private"
        return response


class UserSAMLLoginView(SAMLLoginView):
    def get_auth(self, request):
        return get_auth(request, get_saml_settings_for_request(request))

    def post(self, request):
        response = super(UserSAMLLoginView, self).post(request)
        if SSO_PROVIDER_SESSION_KEY in request.session:
            del request.session[SSO_PROVIDER_SESSION_KEY]
        return response


class SupportSAMLLoginView(SAMLLoginView):
    groups_uri = 'http://schemas.microsoft.com/ws/2008/06/identity/claims/groups'

    def authenticated(self, user, auth, created):
        allowed_groups = set(MemberPlatformSettings.load().support_groups)
        actual_groups = set(auth.attributes[self.groups_uri])

        allowed = len(allowed_groups.intersection(actual_groups)) > 0

        if allowed:
            if not user.is_superuser or not user.is_staff:
                user.is_staff = True
                user.is_superuser = True
                user.save()
        else:
            if created:
                user.delete()

            raise PermissionDenied('Not allowed to login for support')

    def get_auth(self, request):
        saml_request = {
            'https': 'on',
            'http_host': 'sso.goodup.com',
            'script_name': '',
            'get_data': request.GET.copy() or request.POST.copy(),
            'post_data': request.POST.copy(),
        }

        return get_auth(request, self.settings, saml_request=saml_request)

    @property
    def settings(self):
        return settings.SUPPORT_TOKEN_AUTH


class TokenLogoutView(TemplateView):
    """
    Process Single Logout
    FIXME: Not working yet
    """
    query_string = True
    template_name = 'token/token-logout.tpl'

    def get(self, request, *args, **kwargs):
        auth = get_auth(request, settings=get_saml_settings_for_request(request), **kwargs)
        url = auth.process_logout()
        if url:
            return HttpResponseRedirect(url)
        return self.render_to_response({})


class TokenErrorView(TemplateView):

    query_string = True
    template_name = 'token/token-error.tpl'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['message'] = request.GET.get('message', 'Unknown')
        return self.render_to_response(context)


class MetadataView(View):
    """
    Show (SAML) metadata
    """

    def get(self, request, *args, **kwargs):
        auth = get_auth(request, settings=get_saml_settings_for_request(request), **kwargs)
        metadata = auth.get_metadata()
        return HttpResponse(content=metadata, content_type='text/xml')
