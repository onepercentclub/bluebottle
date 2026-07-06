from urllib.parse import urlparse

from django.db import migrations, connection

from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant


def idp_domain_name(idp_sso_url, idp_entity_id):
    for value in (idp_sso_url, idp_entity_id):
        if value and value.startswith('http'):
            netloc = urlparse(value).netloc
            if netloc:
                return netloc
    return idp_entity_id or ''


def import_sso_settings(apps, schema_editor):
    MemberPlatformSettings = apps.get_model('members', 'MemberPlatformSettings')
    SingleSignOnProvider = apps.get_model('members', 'SingleSignOnProvider')
    SingleSignOnAssertionMapping = apps.get_model('members', 'SingleSignOnAssertionMapping')
    SegmentType = apps.get_model('segments', 'SegmentType')

    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    with LocalTenant(tenant):
        if not hasattr(properties, 'TOKEN_AUTH') or not properties.TOKEN_AUTH:
            return

        token_auth_settings = properties.TOKEN_AUTH
        platform_settings, _created = MemberPlatformSettings.objects.get_or_create()
        provider, _created = SingleSignOnProvider.objects.get_or_create(
            settings=platform_settings
        )

        provider.strict = token_auth_settings.get('strict', False)
        provider.debug = token_auth_settings.get('debug', False)
        provider.admin_login = token_auth_settings.get('admin_login', True)
        provider.provision = token_auth_settings.get('provision', True)

        idp = token_auth_settings.get('idp', {})
        provider.idp_entity_id = idp.get('entityId', '')
        provider.idp_x509cert = idp.get('x509cert', '')
        provider.idp_sso_url = idp.get('singleSignOnService', {}).get('url', '')
        provider.idp_sso_binding = idp.get(
            'singleSignOnService', {}
        ).get('binding', 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect')
        provider.idp_sls_url = idp.get('singleLogoutService', {}).get('url', '')
        provider.idp_sls_binding = idp.get(
            'singleLogoutService', {}
        ).get('binding', 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect')

        sp = token_auth_settings.get('sp', {})
        provider.sp_entity_id = sp.get('entityId', '')
        provider.sp_acs_url = sp.get('assertionConsumerService', {}).get('url', '')
        provider.sp_acs_binding = sp.get(
            'assertionConsumerService', {}
        ).get('binding', 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST')
        provider.sp_sls_url = sp.get('singleLogoutService', {}).get('url', '')
        provider.sp_sls_binding = sp.get(
            'singleLogoutService', {}
        ).get('binding', 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect')
        provider.sp_x509cert = sp.get('x509cert', '')
        provider.sp_private_key = sp.get('privateKey', '')

        security = token_auth_settings.get('security', {})
        requested_authn_context = security.get('requestedAuthnContext', False)
        if isinstance(requested_authn_context, bool):
            provider.requested_authn_context = requested_authn_context
        else:
            provider.requested_authn_context = False

        provider.authn_requests_signed = security.get('authnRequestsSigned', False)
        provider.want_assertions_signed = security.get('wantAssertionsSigned', False)

        if not provider.name:
            provider.name = idp_domain_name(provider.idp_sso_url, provider.idp_entity_id)

        provider.save()

        provider.assertion_mappings.all().delete()
        mapping_type_keys = {
            'email': 'email',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'remote_id': 'remote_id',
            'location.name': 'location_name',
            'location.slug': 'location_slug',
        }

        for key, assertion in token_auth_settings.get('assertion_mapping', {}).items():
            if key in mapping_type_keys:
                mapping_type = mapping_type_keys[key]
                segment_type = None
                segment_slug = ''
            elif key.startswith('segment.'):
                mapping_type = 'segment'
                segment_slug = key.replace('segment.', '', 1)
                segment_type = SegmentType.objects.filter(slug=segment_slug).first()
                if segment_type:
                    segment_slug = ''
            else:
                continue

            SingleSignOnAssertionMapping.objects.create(
                provider=provider,
                mapping_type=mapping_type,
                segment_type=segment_type,
                segment_slug=segment_slug,
                assertion=assertion,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0109_alter_member_gender_alter_member_office_manager_and_more'),
    ]

    operations = [
        migrations.RunPython(import_sso_settings, migrations.RunPython.noop),
    ]
