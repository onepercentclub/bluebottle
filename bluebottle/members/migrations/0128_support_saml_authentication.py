import importlib
import logging

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import connection, migrations, models
import django_better_admin_arrayfield.models.fields

logger = logging.getLogger(__name__)

token_auth_migration = importlib.import_module('bluebottle.members.migrations.0125_auto_20261116_1513')
build_idp_metadata = token_auth_migration.build_idp_metadata
USER_FIELD_ATTRIBUTES = token_auth_migration.USER_FIELD_ATTRIBUTES

SUPPORT_ORGANIZATION_NAME = 'GoodUp'
SUPPORT_ORGANIZATION_SLUG = 'goodup'
SUPPORT_GROUP_NAME = 'Staff'


def get_support_token_auth():
    support_token_auth = getattr(settings, 'SUPPORT_TOKEN_AUTH', None)
    if not support_token_auth:
        return None

    idp = support_token_auth.get('idp')
    sp = support_token_auth.get('sp') or {}
    if not idp or not idp.get('singleSignOnService') or not sp.get('entityId'):
        # Not a SAML configuration
        return None

    return support_token_auth


def create_support_saml_authentication(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Group = apps.get_model('auth', 'Group')
    Organization = apps.get_model('organizations', 'Organization')
    SAMLAuthentication = apps.get_model('members', 'SAMLAuthentication')
    SAMLGroupMapping = apps.get_model('members', 'SAMLGroupMapping')
    MemberPlatformSettings = apps.get_model('members', 'MemberPlatformSettings')

    support_token_auth = get_support_token_auth()
    if not support_token_auth:
        return

    idp = support_token_auth['idp']
    sp = support_token_auth['sp']

    if SAMLAuthentication.objects.filter(entity_id=sp['entityId']).exists():
        return

    organization = Organization.objects.filter(slug=SUPPORT_ORGANIZATION_SLUG).first()
    if not organization:
        organization = Organization.objects.create(
            name=SUPPORT_ORGANIZATION_NAME, slug=SUPPORT_ORGANIZATION_SLUG
        )

    vpn_client_ip = getattr(settings, 'VPN_CLIENT_IP', None)
    restricted_ips = [vpn_client_ip] if vpn_client_ip else []
    if not restricted_ips:
        logger.warning('VPN_CLIENT_IP is not set; support SAML authentication is not ip restricted')

    attributes = {field: '' for field in set(USER_FIELD_ATTRIBUTES.values())}
    for target, source in support_token_auth.get('assertion_mapping', {}).items():
        if not source:
            continue

        if target in USER_FIELD_ATTRIBUTES:
            attributes[USER_FIELD_ATTRIBUTES[target]] = source
        else:
            logger.warning('SUPPORT_TOKEN_AUTH: unsupported assertion mapping %s', target)

    method = SAMLAuthentication.objects.create(
        polymorphic_ctype=ContentType.objects.get_for_model(SAMLAuthentication),
        enabled=True,
        entity_id=sp['entityId'],
        organization=organization,
        admin_login_enabled=True,
        provision=True,
        debug=bool(support_token_auth.get('debug', False)),
        strict=bool(support_token_auth.get('strict', False)),
        restricted_ips=restricted_ips,
        **attributes
    )

    if idp.get('x509cert'):
        method.metadata_file.save(
            f'{connection.tenant.client_name}-support-idp-metadata.xml',
            ContentFile(build_idp_metadata(idp, sp.get('NameIDFormat'))),
            save=True
        )
    else:
        logger.warning('SUPPORT_TOKEN_AUTH has no idp certificate; not creating a metadata file')

    member_settings = MemberPlatformSettings.objects.first()
    if member_settings:
        support_groups = member_settings.support_groups
    else:
        support_groups = MemberPlatformSettings._meta.get_field('support_groups').get_default()

    SAMLGroupMapping.objects.create(
        authentication_method=method,
        group=Group.objects.get_or_create(name=SUPPORT_GROUP_NAME)[0],
        group_names=list(support_groups or []),
        staff=True,
        superuser=True,
    )


def remove_support_saml_authentication(apps, schema_editor):
    SAMLAuthentication = apps.get_model('members', 'SAMLAuthentication')

    support_token_auth = get_support_token_auth()
    if not support_token_auth:
        return

    SAMLAuthentication.objects.filter(entity_id=support_token_auth['sp']['entityId']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0127_samlgroupmapping_superuser_alter_member_gender_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='samlauthentication',
            name='restricted_ips',
            field=django_better_admin_arrayfield.models.fields.ArrayField(base_field=models.GenericIPAddressField(), blank=True, default=list, help_text='Restrict access to the method to these IP adresses', size=None, verbose_name='Restricted IP addresses'),
        ),
        migrations.RunPython(create_support_saml_authentication, remove_support_saml_authentication)
    ]
