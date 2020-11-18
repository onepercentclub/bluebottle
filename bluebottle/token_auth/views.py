import re

from django.contrib.auth import login
from django.core.exceptions import ImproperlyConfigured
from django.http.response import HttpResponseRedirect, HttpResponse
from django.template import loader
from django.utils.module_loading import import_string
from django.views.generic.base import View, TemplateView

from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.utils import get_settings


def get_auth(request, **kwargs):
    settings = get_settings()
    try:
        backend = settings['backend']
        if not backend.startswith('bluebottle'):
            backend = 'bluebottle.{}'.format(backend)
    except AttributeError:
        raise ImproperlyConfigured('TokenAuth backend not set')

    try:
        cls = import_string(backend)
    except AttributeError:
        raise ImproperlyConfigured(
            'TokenAuth backend {} is not defined'.format(backend)
        )
    return cls(request, **kwargs)


class TokenRedirectView(View):
    """
    Redirect to SSO login page
    """
    permanent = False
    query_string = True
    pattern_name = 'article-detail'

    def get(self, request, *args, **kwargs):
        auth = get_auth(request, **kwargs)
        sso_url = auth.sso_url(target_url=request.GET.get('url'))
        return HttpResponseRedirect(sso_url)


class TokenLoginView(View):
    """
    Parse GET/POST request and login through set Authentication backend
    """

    def get(self, request, link=None, token=None):
        auth = get_auth(request, token=token, link=link)

        try:
            user, created = auth.authenticate()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
        except TokenAuthenticationError as e:
            url = '/token/error?message={0}'.format(e)
            return HttpResponseRedirect(url)

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

    post = get


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
        auth = get_auth(request, **kwargs)
        context['ssoUrl'] = auth.sso_url()
        return self.render_to_response(context)


class MembersOnlyView(TemplateView):

    query_string = True
    template_name = 'token/members-only.tpl'

    def get(self, request, *args, **kwargs):
        auth = get_auth(request, **kwargs)
        context = self.get_context_data(**kwargs)
        context['url'] = request.GET.get('url', '')
        context['ssoUrl'] = auth.sso_url()
        return self.render_to_response(context)


class MetadataView(View):
    """
    Show (SAML) metadata
    """

    def get(self, request, *args, **kwargs):
        auth = get_auth(request, **kwargs)
        metadata = auth.get_metadata()
        return HttpResponse(content=metadata, content_type='text/xml')
