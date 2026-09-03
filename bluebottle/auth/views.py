from datetime import timedelta

from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from rest_framework.exceptions import AuthenticationFailed
from social_core.exceptions import AuthCanceled
from social_core.utils import get_strategy
from social_django.utils import psa, STORAGE
from two_factor.views import SetupView

from bluebottle.auth.serializers import SocialLoginSerializer
from bluebottle.utils.views import CreateAPIView, JsonApiViewMixin


def load_drf_strategy(request=None):
    return get_strategy('bluebottle.social.strategy.DRFStrategy', STORAGE, request)


@psa(load_strategy=load_drf_strategy)
def complete(request, backend):
    try:
        user = request.backend.complete(request=request)
    except AuthCanceled:
        raise AuthenticationFailed(
            _('Authentication was cancelled'),
            code="cancelled"
        )
    if not user.email:
        if user.date_joined > now() - timedelta(hours=1):
            user.delete()
        raise AuthenticationFailed(
            _('Please allow Facebook access to your email address if you wish to sign up/log in via Facebook.'),
            code="email_required"
        )
    if not user.is_active:
        raise AuthenticationFailed(_('User account is disabled'), code="account_disabled")
    return user


class SocialLoginView(JsonApiViewMixin, CreateAPIView):
    serializer_class = SocialLoginSerializer
    permission_classes = ()

    def perform_create(self, serializer):
        user = complete(self.request, serializer.validated_data['backend'])

        user.last_login = now()
        user.save()

        serializer.instance = type('obj', (object,), {
            'pk': user.id,
            'token': user.get_jwt_token()
        })


@csrf_protect
def admin_password_reset(
    request,
    is_admin_site=False,
    template_name='registration/password_reset_form.html',
    email_template_name='registration/password_reset_email.html',
    subject_template_name='registration/password_reset_subject.txt',
    password_reset_form=PasswordResetForm,
    token_generator=default_token_generator,
    post_reset_redirect=None,
    from_email=None,
    extra_context=None
):
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
