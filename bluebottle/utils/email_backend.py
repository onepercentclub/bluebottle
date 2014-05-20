from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
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
        if request.user.is_authenticated():
            recipient = request.user.email
        else:
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
