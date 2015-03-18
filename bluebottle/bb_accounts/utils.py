import re
from django.template import loader
from django.utils import translation

from bluebottle.clients.utils import tenant_url, tenant_name
from bluebottle.utils.email_backend import send_mail
from bluebottle.clients import properties


def send_welcome_mail(user=None):
    cur_language = translation.get_language()

    if user and user.primary_language:
        translation.activate(user.primary_language)
    else:
        translation.activate(properties.LANGUAGE_CODE)

    c = {
        'email': user.email,
        'site': tenant_url(),
        'site_name': tenant_name(),
        'user': user,
        'first_name': user.first_name,
        'LANGUAGE_CODE': user.primary_language,
    }

    subject_template_name = 'bb_accounts/activation_email_subject.txt'
    subject = loader.render_to_string(subject_template_name, c)

    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    send_mail(
        template_name='bb_accounts/activation_email',
        subject=subject,
        to=user.email,
        **c
    )

    translation.activate(cur_language)


def valid_email(email=None):
    """Returns True if argument is a string with valid email adddress"""
    if not email:
        return False
    pattern = r"[^@]+@[^@]+\.[^@]+"
    p = re.compile(pattern)
    if p.match(email):
        return True
    return False
