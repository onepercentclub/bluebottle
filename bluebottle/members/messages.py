from django.db import connection

from tenant_extras.utils import TenantLanguage
from bluebottle.clients import properties

from bluebottle.notifications.messages import TransitionMessage
from django.utils.translation import ugettext_lazy as _


class SignUptokenMessage(TransitionMessage):
    subject = _('Your activation link for {}')
    template = 'messages/sign_up_token'

    def get_subject(self, language=None):
        if not language:
            language = properties.LANGUAGE_CODE
        with TenantLanguage(language):
            return self.subject.format(connection.tenant.name)

    def get_recipients(self):
        yield self.obj
