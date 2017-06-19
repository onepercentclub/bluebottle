from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from tenant_schemas.middleware import TenantMiddleware
from tenant_schemas.utils import (get_tenant_model, get_public_schema_name)


class DefaultTenantMiddleware(TenantMiddleware):

    def process_request(self, request):
        # Connection needs first to be at the public schema, as this is where
        # the tenant metadata is stored.
        connection.set_schema_to_public()
        hostname = self.hostname_from_request(request)

        TenantModel = get_tenant_model()
        try:
            request.tenant = TenantModel.objects.get(domain_url=hostname)
        except TenantModel.DoesNotExist:
            request.tenant = TenantModel.objects.get(domain_url=settings.DEFAULT_TENANT)

        connection.set_tenant(request.tenant)
        # Content type can no longer be cached as public and tenant schemas
        # have different models. If someone wants to change this, the cache
        # needs to be separated between public and shared schemas. If this
        # cache isn't cleared, this can cause permission problems. For example,
        # on public, a particular model has id 14, but on the tenants it has
        # the id 15. if 14 is cached instead of 15, the permissions for the
        # wrong model will be fetched.
        ContentType.objects.clear_cache()

        # Do we have a public-specific urlconf?
        if hasattr(settings, 'PUBLIC_SCHEMA_URLCONF') and request.tenant.schema_name == get_public_schema_name():
            request.urlconf = settings.PUBLIC_SCHEMA_URLCONF
