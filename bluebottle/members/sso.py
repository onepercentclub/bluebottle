from django.core.exceptions import ImproperlyConfigured


def get_token_auth_settings(tenant_properties=None):
    """
    Return TOKEN_AUTH settings for the current tenant.

    Uses the database configuration when available, otherwise falls back to
    tenant settings.py (during migration).
    """
    from bluebottle.members.models import MemberPlatformSettings, SingleSignOnProvider

    platform_settings = MemberPlatformSettings.load()
    if platform_settings:
        try:
            provider = platform_settings.sso_provider
        except SingleSignOnProvider.DoesNotExist:
            provider = None

        if provider and provider.is_configured:
            return provider.to_token_auth_settings()

    if tenant_properties and 'TOKEN_AUTH' in tenant_properties:
        return tenant_properties['TOKEN_AUTH']

    from django.conf import settings

    if hasattr(settings, 'TOKEN_AUTH'):
        return settings.TOKEN_AUTH

    raise ImproperlyConfigured('Missing TOKEN_AUTH configuration')
