import logging
import re
import dkim

from django.core.mail.backends.smtp import EmailBackend
from django.db import connection
from django.utils import translation
from django.template.loader import get_template

from django_tools.middlewares import ThreadLocal

from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.clients.utils import tenant_url
from bluebottle.clients import properties

from tenant_extras.utils import TenantLanguage

logger = logging.getLogger('console')


class TenantAwareBackend(EmailBackend):
    """
        Support per-tenant smtp configuration and optionally
        sign the message with a DKIM key, if present.
    """

    def open(self):
        tenant_mail_config = getattr(properties, 'MAIL_CONFIG', None)

        if tenant_mail_config:
            # clear everything that was initialized from settings in __init__
            # that is, use the same defaults as django
            self.host = tenant_mail_config.get('HOST', 'localhost')
            self.port = tenant_mail_config.get('PORT', 25)
            self.username = tenant_mail_config.get('USERNAME', '')
            self.password = tenant_mail_config.get('PASSWORD', '')
            self.use_tls = tenant_mail_config.get('TLS', False)
            self.use_ssl = tenant_mail_config.get('SSL', False)

        return super(TenantAwareBackend, self).open()

    def _send(self, email_message):
        """A helper method that does the actual sending + DKIM signing."""
        if not email_message.recipients():
            return False
        try:
            message_string = email_message.message().as_string()
            signature = ""
            try:
                signature = dkim.sign(message_string,
                                      properties.DKIM_SELECTOR,
                                      properties.DKIM_DOMAIN,
                                      properties.DKIM_PRIVATE_KEY)
            except AttributeError:
                pass

            self.connection.sendmail(
                email_message.from_email, email_message.recipients(),
                signature + message_string)
        except:
            if not self.fail_silently:
                raise
            return False
        return True


DKIMBackend = TenantAwareBackend


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


def create_message(template_name=None, to=None, subject=None, cc=None, bcc=None,
                   from_email=None, reply_to=None, **kwargs):

    if hasattr(to, 'primary_language') and to.primary_language:
        language = to.primary_language
    else:
        language = properties.LANGUAGE_CODE

    # This is an exception to handle a Bookingcares.com language which
    # contains more languages than the rest of the platform
    if 'language' in kwargs:
        language = kwargs['language']

    with TenantLanguage(language):
        c = ClientContext(kwargs)
        c['to'] = to  # Add the recipient to the context
        text_content = get_template(
            '{0}.txt'.format(template_name)).render(c)
        html_content = get_template(
            '{0}.html'.format(template_name)).render(c)

        args = dict(subject=subject, body=text_content, to=[to.email])
        if cc:
            args['cc'] = cc
        if bcc:
            args['bcc'] = bcc
        if reply_to:
            args['reply_to'] = [reply_to]

        # even if it's None
        args['from_email'] = from_email

        # Calling force_unicode on the subject below in case the subject
        # is being translated using ugettext_lazy.
        msg = EmailMultiAlternatives(**args)
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

    if not kwargs.get('site'):
        kwargs.update({
            'site': tenant_url()
        })

    try:
        msg = create_message(template_name=template_name,
                             to=to,
                             subject=subject,
                             **kwargs)
    except Exception as e:
        msg = None
        logger.error("Exception while rendering email template: {0}".format(e))
        return

    # Explicetly set CELERY usage in properties. Used primarily for
    # testing purposes.
    try:
        tenant = connection.tenant
    except AttributeError:
        tenant = None

    if msg and properties.CELERY_MAIL:
        if properties.SEND_MAIL:
            _send_celery_mail.delay(msg, tenant, send=True)
        else:
            _send_celery_mail.delay(msg, tenant)
    elif msg:
        try:
            if properties.SEND_MAIL:
                msg.send()
            else:
                logger.info("Tried to send async email, " +
                            "but mail sending is turned off.")
        except Exception as e:
            logger.error("Exception sending synchronous email: {0}".format(e))
            return
