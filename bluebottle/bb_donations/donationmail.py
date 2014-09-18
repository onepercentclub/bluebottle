from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from django.utils import translation
from django.template.loader import get_template


def successful_donation_fundraiser_mail(instance):

    # should be only when the status is success
    try:
        receiver = instance.fundraiser.owner
    except:
        # donation it's not coming from a fundraiser
        return
    fundraiser_link = '/go/fundraisers/{0}'.format(instance.fundraiser.id)
    context = Context({'amount': instance.amount,
                       'site': 'https://' + Site.objects.get_current().domain,
                       'link': fundraiser_link,
                       'receiver': receiver.get_short_name()
                       })
    subject = _('You received a new donation')
    translation.activate(receiver.primary_language)
    translation.deactivate()
    text_content = get_template('new_oneoff_donation_fundraiser.mail.txt').render(context)
    html_content = get_template('new_oneoff_donation_fundraiser.mail.html').render(context)
    msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

