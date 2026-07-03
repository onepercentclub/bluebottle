# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('segments', '0036_auto_20251216_1447'),
        ('members', '0107_merge_20260224_1343'),
    ]

    operations = [
        migrations.CreateModel(
            name='SingleSignOnProvider',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backend', models.CharField(default='token_auth.auth.saml.SAMLAuthentication', max_length=255, verbose_name='Authentication backend')),
                ('strict', models.BooleanField(default=False, verbose_name='Strict mode')),
                ('debug', models.BooleanField(default=False, verbose_name='Debug mode')),
                ('admin_login', models.BooleanField(default=True, help_text='When enabled, staff can log in to the admin via SSO.', verbose_name='Allow admin login via SSO')),
                ('provision', models.BooleanField(default=True, help_text='Automatically create member accounts on first SSO login.', verbose_name='Auto-provision users')),
                ('idp_entity_id', models.CharField(blank=True, max_length=500, verbose_name='IdP entity ID')),
                ('idp_x509cert', models.TextField(blank=True, verbose_name='IdP x509 certificate')),
                ('idp_sso_url', models.URLField(blank=True, max_length=500, verbose_name='IdP single sign-on URL')),
                ('idp_sso_binding', models.CharField(default='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect', max_length=255, verbose_name='IdP SSO binding')),
                ('idp_sls_url', models.URLField(blank=True, max_length=500, verbose_name='IdP single logout URL')),
                ('idp_sls_binding', models.CharField(default='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect', max_length=255, verbose_name='IdP SLO binding')),
                ('sp_entity_id', models.CharField(blank=True, max_length=500, verbose_name='SP entity ID')),
                ('sp_name_id_format', models.CharField(choices=[('urn:oasis:names:tc:SAML:2.0:nameid-format:string', 'String'), ('urn:oasis:names:tc:SAML:2.0:nameid-format:persistent', 'Persistent'), ('urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified', 'Unspecified'), ('urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress', 'Email address')], default='urn:oasis:names:tc:SAML:2.0:nameid-format:string', max_length=255, verbose_name='SP NameID format')),
                ('sp_acs_url', models.URLField(blank=True, help_text='Typically https://your-domain/token/login/', max_length=500, verbose_name='SP assertion consumer URL')),
                ('sp_acs_binding', models.CharField(default='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST', max_length=255, verbose_name='SP ACS binding')),
                ('sp_sls_url', models.URLField(blank=True, help_text='Typically https://your-domain/token/logout/', max_length=500, verbose_name='SP single logout URL')),
                ('sp_sls_binding', models.CharField(default='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect', max_length=255, verbose_name='SP SLO binding')),
                ('sp_x509cert', models.TextField(blank=True, verbose_name='SP x509 certificate')),
                ('sp_private_key', models.TextField(blank=True, verbose_name='SP private key')),
                ('requested_authn_context', models.BooleanField(default=False, help_text='Disable for most Azure AD / Entra ID integrations.', verbose_name='Request authentication context')),
                ('requested_authn_context_comparison', models.CharField(blank=True, max_length=50, verbose_name='Requested authentication context comparison')),
                ('authn_requests_signed', models.BooleanField(default=False, verbose_name='Sign authentication requests')),
                ('want_assertions_signed', models.BooleanField(default=False, verbose_name='Require signed assertions')),
                ('security_overrides', models.JSONField(blank=True, help_text='Optional JSON for uncommon python-saml security settings.', null=True, verbose_name='Security overrides')),
                ('settings', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='sso_provider', to='members.memberplatformsettings')),
            ],
            options={
                'verbose_name': 'Single sign-on provider',
                'verbose_name_plural': 'Single sign-on providers',
            },
        ),
        migrations.CreateModel(
            name='SingleSignOnAssertionMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mapping_type', models.CharField(choices=[('email', 'Email'), ('first_name', 'First name'), ('last_name', 'Last name'), ('remote_id', 'Remote ID'), ('location_name', 'Location name'), ('location_slug', 'Location slug'), ('segment', 'Segment')], max_length=50, verbose_name='Member field')),
                ('segment_slug', models.CharField(blank=True, help_text='Used when the segment type is not linked yet.', max_length=100, verbose_name='Segment type slug')),
                ('assertion', models.CharField(max_length=500, verbose_name='SAML assertion')),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assertion_mappings', to='members.singlesignonprovider')),
                ('segment_type', models.ForeignKey(blank=True, help_text='Required for segment mappings.', null=True, on_delete=django.db.models.deletion.CASCADE, to='segments.segmenttype')),
            ],
            options={
                'verbose_name': 'SSO assertion mapping',
                'verbose_name_plural': 'SSO assertion mappings',
                'unique_together': {('provider', 'mapping_type', 'segment_type', 'segment_slug')},
            },
        ),
    ]
