from django.conf import settings
from django.db import models, connection
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings

import hmac
import hashlib
import base64


class CommonPlatformSettings(BasePlatformSettings):
    lockdown = models.BooleanField(default=False,
                                   help_text=_('Checking this will lockdown the site with the provided password.'))
    lockdown_password = models.CharField(null=True, blank=True, max_length=100,
                                         help_text=_('This is the password clients need to enter to view the site.'))

    @property
    def token(self):
        message = "{}{}".format(connection.tenant.name, self.lockdown_password)
        digest = hmac.new(settings.SECRET_KEY, msg=message, digestmod=hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    def generate_token(self, request):
        message = "{}{}".format(request.session_id, self.lockdown_password)
        digest = hmac.new(settings.SECRET_KEY, msg=message, digestmod=hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    class Meta:
        verbose_name_plural = _('common platform settings')
        verbose_name = _('common platform settings')
