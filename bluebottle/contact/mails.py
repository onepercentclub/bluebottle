from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.template import Context
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _



def send_contact_email(message, contact_email):
    subject = _('Contact message from %(sender)s') % {'sender': message.name}
    from_email = message.email
    site = Site.objects.get_current()
    site_url = 'https://' + site.domain

    # add the url to the backoffice
    link = reverse('admin:contact_contactmessage_change', args=[message.id])

    ctx = Context({'message': message, 'link': link, 'site_url': site_url, 'site': site})

    text_content = render_to_string('contact/contact.mail.txt', context_instance=ctx)
    html_content = render_to_string('contact/contact.mail.html', context_instance=ctx)


    msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[contact_email], from_email=from_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()