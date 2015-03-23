import logging
import re
import dkim

from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
from django.utils import translation
from django.template.loader import get_template
from django_tools.middlewares import ThreadLocal

from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.clients import properties


logger = logging.getLogger()


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
            self.connection.sendmail(
                email_message.from_email, email_message.recipients(),
                signature + message_string)
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
            email_message.subject += ' || To: ' + \
                str(email_message.recipients()[0])
            message_string = email_message.message().as_string()

            self.connection.sendmail(
                email_message.from_email, recipient, message_string)
        except:
            if not self.fail_silently:
                raise
            return False
        return True


def create_message(template_name=None, to=None, subject=None, **kwargs):

    if hasattr(to, 'primary_language') and to.primary_language:
        language = to.primary_language
    else:
        language = properties.LANGUAGE_CODE

    translation.activate(language)

    c = ClientContext(kwargs)
    text_content = get_template(
        '{0}.txt'.format(template_name)).render(c)
    html_content = get_template(
        '{0}.html'.format(template_name)).render(c)
    msg = EmailMultiAlternatives(subject=subject,
                                 body=text_content,
                                 to=[to.email])
    msg.activated_language = translation.get_language()
    msg.attach_alternative(html_content, "text/html")
    return msg


# We need a wrapper outside of Celery to prepare the email because
# Celery is not tenant aware.
def send_mail(template_name=None, subject=None, to=None, **kwargs):
    from bluebottle.common.tasks import _send_celery_mail

    if not to:
        logger.error("No recipient specified")
        return

    # Simple check if email address is valid
    regex = r'[^@]+@[^@]+\.[^@]+'
    if not re.match(regex, to.email):
        logger.error("Trying to send email to invalid email address: {0}"
                     .format(to.email))
        return

    try:
        msg = create_message(template_name=template_name,
                             to=to,
                             subject=subject,
                             **kwargs)
    except Exception as e:
        msg = None
        logger.error("Exception while rendering email template: {0}".format(e))
        return
    finally:
        translation.deactivate()

    # Explicetly set CELERY usage in settings. Used primarily for
    # testing purposes.
    if msg and properties.CELERY_MAIL:
        if properties.SEND_MAIL:
            _send_celery_mail.delay(msg, send=True)
        else:
            _send_celery_mail.delay(msg)
    elif msg:
        try:
            if properties.SEND_MAIL:
                msg.send()
            else:
                logger.info("Tried to send async email, but mail sending is\
                            turned off. ")
        except Exception as e:
            logger.error("Exception sending synchronous email: {0}".format(e))
            return
