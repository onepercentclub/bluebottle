import re

from django.utils.http import int_to_base36
from django.contrib.auth.tokens import default_token_generator

from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url, tenant_name
from bluebottle.members.messages import AccountActivationMessage


def send_welcome_mail(user=None):

    from bluebottle.members.models import MemberPlatformSettings
    settings = MemberPlatformSettings.objects.get()

    context = {
        'email': user.email,
        'site': tenant_url(),
        'site_name': tenant_name(),
        'user': user,
        'first_name': user.first_name,
        'contact_email': properties.CONTACT_EMAIL,
        'closed_site': settings.closed,
        'LANGUAGE_CODE': user.primary_language,
    }

    # If there is no password and no remote_id (SSO) then use the
    # welcome + password template, and then set a random password
    if not user.password and not user.remote_id:
        context.update({
            'token': default_token_generator.make_token(user),
            'uid': int_to_base36(user.pk),
        })

    msg = AccountActivationMessage(user, context=context)
    msg.compose_and_send()

    user.welcome_email_is_sent = True
    user.save()


def valid_email(email=None):
    """Returns True if argument is a string with valid email adddress"""
    if not email:
        return False
    pattern = r"[^@]+@[^@]+\.[^@]+"
    pat = re.compile(pattern)
    if pat.match(email):
        return True
    return False
