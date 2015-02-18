from django.contrib.sites.models import Site
from django.template.loader import get_template
from django.utils import translation

from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.clients import properties


def send_mail(template_name, subject, to, **kwargs):
    if hasattr(to, 'primary_language') and to.primary_language:
        translation.activate(to.primary_language)

    kwargs.update({
        'receiver': to,
        'site': 'https://{0}'.format(Site.objects.get_current().domain)
    })

    context = ClientContext(kwargs)
    subject = unicode(subject)  # Unlazy the translatable string subject within activated language.

    text_content = get_template('{0}.txt'.format(template_name)).render(context)
    html_content = get_template('{0}.html'.format(template_name)).render(context)

    if hasattr(to, 'primary_language') and to.primary_language:
        translation.deactivate()

    from_email = properties.CONTACT_EMAIL

    msg = EmailMultiAlternatives(subject=subject, from_email=from_email, body=text_content, to=[to.email])
    msg.attach_alternative(html_content, "text/html")

    return msg.send()
