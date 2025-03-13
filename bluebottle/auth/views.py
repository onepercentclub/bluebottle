from django import forms
from django.shortcuts import resolve_url
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.db import connection
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import parsers, renderers

from two_factor.views import SetupView

from social_django.utils import psa, get_strategy, STORAGE
from social.exceptions import AuthCanceled

from bluebottle.auth.serializers import FacebookAuthSerializer
from bluebottle.utils.views import CreateAPIView, JsonApiViewMixin


class GetAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser,
                      parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer
    queryset = Token.objects.all()

    # Accept backend as a parameter and 'auth' for a login / pass
    def post(self, request, backend):
        # Here we call PSA to authenticate like we would if we used PSA on
        # server side.
        token_result = complete(request, backend)

        # If user is active we get or create the REST token and send it back
        # with user data
        if token_result.get('token', None):
            return Response({'token': token_result.get('token')})
        elif token_result.get('error', None):
            return Response({'error': token_result.get('error')})
        return Response({'error': _('No result for token')})


def load_drf_strategy(request=None):
    return get_strategy('bluebottle.social.strategy.DRFStrategy', STORAGE, request)


@psa(redirect_uri='/static/assets/frontend/popup.html',
     load_strategy=load_drf_strategy)
def complete(request, backend):
    try:
        user = request.backend.auth_complete(request=request)
    except AuthCanceled:
        return None

    if user and user.is_active:
        user.last_login = now()
        user.save()
        return {'token': user.get_jwt_token()}
    elif user and not user.is_active:
        return {'error': _(
            "This user account is disabled, please contact us if you want to re-activate.")}
    else:
        return None


class AuthFacebookView(JsonApiViewMixin, CreateAPIView):
    serializer_class = FacebookAuthSerializer
    permission_classes = ()


@csrf_protect
def admin_password_reset(request, is_admin_site=False,
                         template_name='registration/password_reset_form.html',
                         email_template_name='registration/password_reset_email.html',
                         subject_template_name='registration/password_reset_subject.txt',
                         password_reset_form=PasswordResetForm,
                         token_generator=default_token_generator,
                         post_reset_redirect=None,
                         from_email=None,
                         extra_context=None):
    """
    This is a copy of django.contrib.auth.views.password_reset but this
    forces the domain to the one specified in current tenant.
    """

    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_done')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)

    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'token_generator': token_generator,
                'from_email': from_email,
                'email_template_name': email_template_name,
                'subject_template_name': subject_template_name,
                'request': request,
            }
            tenant = connection.get_tenant()
            domain_override = tenant.domain_url
            opts = dict(opts, domain_override=domain_override)
            form.save(**opts)
            return HttpResponseRedirect(post_reset_redirect)
    else:
        form = password_reset_form()
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context)


@never_cache
@require_http_methods(['POST'])
@csrf_protect
def admin_logout(request, extra_context=None):
    """
    Log out the user for the given HttpRequest.

    This should *not* assume the user is already logged in.
    """
    from django.contrib.auth.views import LogoutView
    defaults = {
        'extra_context': {
            # Since the user isn't logged out at this point, the value of
            # has_permission must be overridden.
            'has_permission': False,
            **(extra_context or {})
        },
    }
    return LogoutView.as_view(**defaults)(request)


class MethodForm(forms.Form):
    method = forms.ChoiceField(
        label=_("Authentication method"),
        widget=forms.RadioSelect
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        method = self.fields['method']

        method.choices = [
            (
                'generator',
                mark_safe(
                    _(
                        '<b>Authentication app</b>'
                        '<p style="padding-top: 0px; padding-left: 24px;">'
                        'Generate secure codes using an app like Google Authenticator or Authy.'
                        '</p>'
                    )
                ),
            ),
            (
                'sms',
                mark_safe(
                    _(
                        '<b>Text Message (SMS)</b>'
                        '<p style="padding-top: 0px; padding-left: 24px;">'
                        'enter your phone number and receive verification codes via SMS.'
                        '</p>'
                    )
                )
            ),
        ]
        method.initial = method.choices[0][0]


class TwoFactorSetupView(SetupView):
    success_url = 'admin:index'
    form_list = (
        ('welcome', forms.Form),
        ('method', MethodForm),
        # Other forms are dynamically added in get_form_list()
    )
