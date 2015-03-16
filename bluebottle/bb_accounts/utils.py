import re
from django.template import loader
from django.utils import translation

from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.clients.utils import tenant_url, tenant_name

from bluebottle.clients import properties


def send_welcome_mail(user=None):
    cur_language = translation.get_language()

    if user and user.primary_language:
        translation.activate(user.primary_language)
    else:
        translation.activate(properties.LANGUAGE_CODE)

    c = ClientContext({
        'email': user.email,
        'site': tenant_url(),
        'site_name': tenant_name(),
        'user': user,
        'first_name': user.first_name,
        'LANGUAGE_CODE': user.primary_language,
    })

    subject_template_name = 'bb_accounts/activation_email_subject.txt'

    # XXX TODO: restore plaintext alternative, like most other mails
    email_template_name = 'bb_accounts/activation_email.html'
    email_template_name_txt = 'bb_accounts/activation_email.txt'

    subject = loader.render_to_string(subject_template_name, c)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    email = loader.render_to_string(email_template_name, c)
    email_txt = loader.render_to_string(email_template_name_txt, c)

    try:
        msg = EmailMultiAlternatives(subject=subject, body=email_txt,
                                     to=[user.email])
        msg.attach_alternative(email, "text/html")
        msg.send()
    finally:
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
