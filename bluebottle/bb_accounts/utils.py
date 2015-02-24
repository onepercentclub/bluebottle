import re
from django.conf import settings
from django.template import loader
from django.contrib.sites.models import Site

from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import construct_from_header

def send_welcome_mail(user=None):
    current_site = Site.objects.get_current()
    site_name = current_site.name
    domain = current_site.domain
    site = 'https://' + domain

    c = ClientContext({
        'email': user.email,
        'site': site,
        'site_name': site_name,
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
    
