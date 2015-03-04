import re
from django.conf import settings
from django.template import loader

from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import construct_from_header
from bluebottle.clients.utils import tenant_url, tenant_name

def send_welcome_mail(user=None):
    c = ClientContext({
        'email': user.email,
        'site': tenant_url(),
        'site_name': tenant_name(),
        'user': user,
        'LANGUAGE_CODE': user.primary_language
    })

    subject_template_name = 'bb_accounts/activation_email_subject.txt'

    # XXX TODO: restore plaintext alternative, like most other mails
    email_template_name = 'bb_accounts/activation_email.html'

    subject = loader.render_to_string(subject_template_name, c)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    email = loader.render_to_string(email_template_name, c)

    tenant_from = construct_from_header()
    user.email_user(subject, email, from_email=tenant_from)

def valid_email(email=None):
    """Returns True if argument is a string with valid email adddress"""
    if not email:
        return False
    pattern = r"[^@]+@[^@]+\.[^@]+"
    p = re.compile(pattern)
    if p.match(email):
        return True
    return False
    
