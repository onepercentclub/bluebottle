import re

from django.utils.translation import ugettext_lazy as _
from django.utils.http import int_to_base36
from django.contrib.auth.tokens import default_token_generator

from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url, tenant_name
from bluebottle.utils.email_backend import send_mail

from tenant_extras.utils import TenantLanguage


def send_welcome_mail(user=None):
    subject = _("Welcome to %(site_name)s") % {'site_name': tenant_name()}
    if user and user.primary_language:
        with TenantLanguage(user.primary_language):
            subject = _("Welcome to %(site_name)s") % {'site_name': tenant_name()}

    data = {
        'email': user.email,
        'site': tenant_url(),
        'site_name': tenant_name(),
        'user': user,
        'first_name': user.first_name,
        'contact_email': properties.CONTACT_EMAIL,
        'token': default_token_generator.make_token(user),
        'uid': int_to_base36(user.pk),
        'LANGUAGE_CODE': user.primary_language,
    }

    # If there is no password and no remote_id (SSO) then use the
    # welcome + password template, and then set a random password
    if not user.password and not user.remote_id:
        send_mail(
            template_name='bb_accounts/activation_email_no_password',
            subject=subject,
            to=user,
            **data
        )
    else:
        send_mail(
            template_name='bb_accounts/activation_email',
            subject=subject,
            to=user,
            **data
        )


def valid_email(email=None):
    """Returns True if argument is a string with valid email adddress"""
    if not email:
        return False
    pattern = r"[^@]+@[^@]+\.[^@]+"
    pat = re.compile(pattern)
    if pat.match(email):
        return True
    return False
