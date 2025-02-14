import re

from bluebottle.clients import properties

from django.conf import settings
from django.contrib.auth import login
from django.http.response import HttpResponseRedirect, HttpResponse
from django.template import loader
from django.views.generic.base import View, TemplateView

from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.auth.saml import SAMLAuthentication


def get_auth(request, settings, saml_request=None):
    return SAMLAuthentication(request, settings, saml_request=saml_request)


class TokenRedirectView(View):
    """
    Redirect to SSO login page
    """
    permanent = False
    query_string = True
    pattern_name = 'article-detail'

    def get(self, request, *args, **kwargs):
        auth = get_auth(request, settings=properties.TOKEN_AUTH, **kwargs)
        sso_url = auth.sso_url(target_url=request.GET.get('url'))
        return HttpResponseRedirect(sso_url)


class SAMLLoginView(View):
    def get_auth(self, request):
        return get_auth(request, self.settings)

    def authenticated(self, user):
        pass

    def post(self, request):
        auth = self.get_auth(request)

        try:
            user, created = auth.authenticate()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
        except TokenAuthenticationError as e:
            url = '/token/error?message={0}'.format(e)
            return HttpResponseRedirect(url)

        self.authenticated(user)

        target_url = auth.target_url or "/"

        if target_url and re.match('^\/\w\w\/admin', target_url):
            # Admin login:
            # Log user in using cookies and redirect directly
            login(request, user)
            return HttpResponseRedirect(target_url)

        template = loader.get_template('utils/login_with.html')
        context = {'token': user.get_jwt_token(), 'link': target_url}
        response = HttpResponse(template.render(context, request), content_type='text/html')
        response['cache-control'] = "no-store, no-cache, private"
        return response


class UserSAMLLoginView(SAMLLoginView):
    @property
    def settings(self):
        return properties.TOKEN_AUTH


class SupportSAMLLoginView(SAMLLoginView):
    def authenticated(self, user):

        if not user.is_superuser or not user.is_staff:
            user.is_staff = True
            user.is_superuser = True
            user.save()

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
        auth = get_auth(request, **kwargs)
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
        auth = get_auth(request, **kwargs)
        metadata = auth.get_metadata()
        return HttpResponse(content=metadata, content_type='text/xml')
