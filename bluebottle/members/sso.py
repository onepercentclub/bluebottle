from django.core.exceptions import ImproperlyConfigured


def get_configured_sso_providers():
    from bluebottle.members.models import MemberPlatformSettings

    platform_settings = MemberPlatformSettings.load()
    if not platform_settings:
        return []

    return [
        provider for provider in platform_settings.sso_providers.all()
        if provider.is_configured
    ]


def get_sso_provider(provider_id=None, require=False):
    providers = get_configured_sso_providers()

    if provider_id:
        for provider in providers:
            if str(provider.pk) == str(provider_id):
                return provider
        raise ImproperlyConfigured('Unknown SSO provider: {}'.format(provider_id))

    if len(providers) == 1:
        return providers[0]

    if require and len(providers) > 1:
        raise ImproperlyConfigured(
            'SSO provider id is required when multiple providers are configured'
        )

    return None


def get_token_auth_settings(tenant_properties=None, provider_id=None):
    """
    Return TOKEN_AUTH settings for the current tenant.

    Uses the database configuration when available, otherwise falls back to
    tenant settings.py (during migration).
    """
    if provider_id:
        provider = get_sso_provider(provider_id)
        if provider:
            return provider.to_token_auth_settings()
    else:
        providers = get_configured_sso_providers()
        if providers:
            return providers[0].to_token_auth_settings()

    if tenant_properties and 'TOKEN_AUTH' in tenant_properties:
        return tenant_properties['TOKEN_AUTH']

    from django.conf import settings

    if hasattr(settings, 'TOKEN_AUTH'):
        return settings.TOKEN_AUTH

    raise ImproperlyConfigured('Missing TOKEN_AUTH configuration')
