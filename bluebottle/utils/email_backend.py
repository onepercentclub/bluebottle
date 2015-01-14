from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from django.utils import translation
from django.template.loader import get_template
from django.utils import translation
import dkim
from django_tools.middlewares import ThreadLocal


class DKIMBackend(EmailBackend):
    def _send(self, email_message):
        """A helper method that does the actual sending + DKIM signing."""
        if not email_message.recipients():
            return False
        try:
            message_string = email_message.message().as_string()
            signature = dkim.sign(message_string,
                                  settings.DKIM_SELECTOR,
                                  settings.DKIM_DOMAIN,
                                  settings.DKIM_PRIVATE_KEY)
            self.connection.sendmail(email_message.from_email, email_message.recipients(), signature+message_string)
        except:
            if not self.fail_silently:
                raise
            return False
        return True


class TestMailBackend(EmailBackend):
    def _send(self, email_message):
        """ Force recipient to the current user."""
        request = ThreadLocal.get_current_request()

        try:
            request.user.is_authenticated()
            recipient = request.user.email
        except:
            recipient = str(email_message.recipients()[0])
            if '+test' not in recipient:
                return False

        try:
            email_message.subject += ' || To: ' + str(email_message.recipients()[0])
            message_string = email_message.message().as_string()

            self.connection.sendmail(email_message.from_email, recipient, message_string)
        except:
            if not self.fail_silently:
                raise
            return False
        return True

def send_mail(template_name, subject, to, cc=None, bcc=None, **kwargs):
    if hasattr(to, 'primary_language') and to.primary_language:
        translation.activate(to.primary_language)

    kwargs.update({
        'receiver': to,
        'site': 'https://{0}'.format(Site.objects.get_current().domain)
    })

    context = Context(kwargs)
    subject = unicode(subject)  # Unlazy the translatable string subject within activated language.

    text_content = get_template('{0}.txt'.format(template_name)).render(context)
    html_content = get_template('{0}.html'.format(template_name)).render(context)

    if hasattr(to, 'primary_language') and to.primary_language:
        translation.deactivate()

    args = dict(subject=subject, body=text_content, to=[to.email])
    if cc:
        args['cc'] = cc
    if bcc:
        args['bcc'] = bcc

    msg = EmailMultiAlternatives(**args)

    msg.attach_alternative(html_content, "text/html")

    return msg.send()
