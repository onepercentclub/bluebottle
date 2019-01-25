import urllib

from django.http.response import HttpResponseRedirect, HttpResponse
from django.views.generic.base import View, TemplateView
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured

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
        except TokenAuthenticationError, e:
            url = '/token/error?message={0}'.format(e)
            return HttpResponseRedirect(url)

        url = "/login-with/{}/{}".format(user.pk, user.get_login_token())

        if link:
            url += '?{}'.format(urllib.urlencode({'next': link}))
        elif auth.target_url:
            url += '?{}'.format(urllib.urlencode({'next': auth.target_url}))

        return HttpResponseRedirect(url)

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
        return self.render_to_response()


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
