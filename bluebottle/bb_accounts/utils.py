import re

from django.utils.translation import ugettext_lazy as _

from bluebottle.clients.utils import tenant_url, tenant_name
from bluebottle.utils.email_backend import send_mail

from tenant_extras.utils import TenantLanguage


def send_welcome_mail(user=None):
    subject = _("Welcome to %(site_name)s") % {'site_name': tenant_name()}
    if user and user.primary_language:
        with TenantLanguage(user.primary_language):
            subject = _("Welcome to %(site_name)s") % {'site_name': tenant_name()}

    c = {
        'email': user.email,
        'site': tenant_url(),
        'site_name': tenant_name(),
        'user': user,
        'first_name': user.first_name,
        'LANGUAGE_CODE': user.primary_language,
    }

    send_mail(
        template_name='bb_accounts/activation_email',
        subject=subject,
        to=user,
        **c
    )


def valid_email(email=None):
    """Returns True if argument is a string with valid email adddress"""
    if not email:
        return False
    pattern = r"[^@]+@[^@]+\.[^@]+"
    p = re.compile(pattern)
    if p.match(email):
        return True
    return False
