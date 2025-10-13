from urllib.parse import urljoin

from django.db import models
from django.utils.translation import gettext_lazy as _

from future.utils import python_2_unicode_compatible
from tenant_schemas.models import TenantMixin
from django.conf import settings


@python_2_unicode_compatible
class Client(TenantMixin):
    name = models.CharField(max_length=100)
    client_name = models.CharField(max_length=100, unique=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)

    auto_create_schema = True

    def build_absolute_url(self, path):
        if getattr(settings, 'TESTING', False):
            scheme = 'http'
        elif 'localhost' in self.domain_url:
            return urljoin(f'http://{self.domain_url}:3000', path)
        else:
            scheme = 'https'

        return urljoin(f'{scheme}://{self.domain_url}', path)

    def __str__(self):
        return self.name
