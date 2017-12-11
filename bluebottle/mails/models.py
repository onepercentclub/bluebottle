from django.db import models, connection
from django.utils.translation import ugettext_lazy as _

from bluebottle.utils.models import BasePlatformSettings


class MailPlatformSettings(BasePlatformSettings):
    email_logo = models.ImageField(null=True, blank=True, upload_to='site_content/')

    def email_logo_url(self):
        if 'localhost' in connection.tenant.domain_url:
            logo_url = 'http://' + connection.tenant.domain_url + ':4200' + self.email_logo.url
        else:
            logo_url = 'https://' + connection.tenant.domain_url + self.email_logo.url
        return logo_url

    class Meta:
        verbose_name_plural = _('mail platform settings')
        verbose_name = _('mail platform settings')
