import logging
import re

import django_otp
from django.contrib.auth import login
from django.http.response import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.template import loader
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic.base import View, TemplateView

from rest_framework.generics import get_object_or_404

from onelogin.saml2.response import OneLogin_Saml2_Response

from bluebottle.members.models import SAMLAuthentication as SAMLAuthenticationMethod
from bluebottle.token_auth.auth.saml import SAMLAuthentication
from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.models import SAMLDevice
from bluebottle.utils.utils import get_client_ip

logger = logging.getLogger(__name__)


class TokenRedirectView(View):
    """
    Redirect to SSO login page
    """
    def target_url(self, request):
        url = request.GET.get('url')

        try:
            allowed = url and url_has_allowed_host_and_scheme(
                url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            )
            if allowed:
                return request.build_absolute_uri(url)
        except ValueError:
            allowed = False

        if url:
            logger.warning(
                'Rejected off-site or malformed token redirect url %r on %s',
                url,
                request.get_host(),
            )
        return request.build_absolute_uri('/')

    def get(self, request, *args, **kwargs):
        client_ip = get_client_ip(request)

        method = get_object_or_404(
            SAMLAuthenticationMethod.objects.exclude(
                metadata_file='',
            ),
            pk=kwargs['pk'],
            metadata_file__isnull=False,
            enabled=True
        )

        auth = SAMLAuthentication(request, method.settings)
        sso_url = auth.sso_url(target_url=self.target_url(request))
        return HttpResponseRedirect(sso_url)


class SAMLLoginView(View):
    def get_method(self):
        response = OneLogin_Saml2_Response({}, self.request.POST['SAMLResponse'])
        methods = SAMLAuthenticationMethod.objects.filter(
            entity_id__in=response.get_audiences(), enabled=True
        )

        for method in methods:
            if method.idp_entity_id in response.get_issuers():
                return method

    def post(self, request):
        method = self.get_method()

        if not method:
            return HttpResponseForbidden('Unknown audience or issuer')

        auth = SAMLAuthentication(request, method.settings)

        try:
            user, _created = auth.authenticate()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
        except TokenAuthenticationError as e:
            url = '/token/error?message={0}'.format(e)
            return HttpResponseRedirect(url)

        target_url = auth.target_url or "/"

        if target_url and re.match(r'^/\w\w/admin', target_url):
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


class TokenLogoutView(TemplateView):
    """
    Process Single Logout
    FIXME: Not working yet
    """
    query_string = True
    template_name = 'token/token-logout.tpl'

    def get(self, request, *args, **kwargs):
        auth = SAMLAuthentication(request)
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
        method = get_object_or_404(SAMLAuthenticationMethod, pk=kwargs['pk'])
        auth = SAMLAuthentication(request, method.settings)

        return HttpResponse(content=auth.get_metadata(), content_type='text/xml')
