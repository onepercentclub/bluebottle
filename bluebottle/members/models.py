from __future__ import absolute_import

from builtins import object
from datetime import timedelta, datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_email
from django.db import models
from django.db.models import Sum, CharField
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField
from future.utils import python_2_unicode_compatible
from multiselectfield import MultiSelectField
from parler.models import TranslatableModel, TranslatedFields

from bluebottle.bb_accounts.models import BlueBottleBaseUser
from bluebottle.files.fields import ImageField
from bluebottle.geo.models import Place, Location
from bluebottle.utils.fields import CheckboxField
from bluebottle.utils.models import BasePlatformSettings
from bluebottle.utils.validators import FileMimetypeValidator, validate_file_infection
from ..offices.models import OfficeSubRegion
from ..segments.models import SegmentType, Segment


def default_support_groups():
    return ['Engineering Team', 'Support']


class SocialLoginSettings(models.Model):
    LOGIN_BACKENDS = (
        ('facebook', _('Facebook')),
        ('google', _('Google')),
    )
    settings = models.ForeignKey(
        'members.MemberPlatformSettings',
        on_delete=models.CASCADE,
        related_name='social_login_methods'
    )

    backend = models.CharField(_('Platform'), choices=LOGIN_BACKENDS)
    secret = models.CharField(_('Secret'))
    client_id = models.CharField(_('Client id'))

    class Meta(object):
        verbose_name_plural = _('Social login settings')
        verbose_name = _('Social login settings')


SAML_BINDING_HTTP_POST = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
SAML_BINDING_HTTP_REDIRECT = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'

SAML_NAME_ID_FORMATS = (
    ('urn:oasis:names:tc:SAML:2.0:nameid-format:string', _('String')),
    ('urn:oasis:names:tc:SAML:2.0:nameid-format:persistent', _('Persistent')),
    ('urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified', _('Unspecified')),
    ('urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress', _('Email address')),
)


class SingleSignOnProvider(models.Model):
    """
    SAML SSO configuration for a tenant. Replaces TOKEN_AUTH in tenant settings.py.
    """
    settings = models.ForeignKey(
        'members.MemberPlatformSettings',
        on_delete=models.CASCADE,
        related_name='sso_providers',
    )

    backend = models.CharField(
        _('Authentication backend'),
        max_length=255,
        default='token_auth.auth.saml.SAMLAuthentication',
    )

    strict = models.BooleanField(_('Strict mode'), default=False)
    debug = models.BooleanField(_('Debug mode'), default=False)
    admin_login = models.BooleanField(
        _('Admin login'),
        default=True,
        help_text=_('When enabled, staff can log in to the admin via SSO.'),
    )
    provision = models.BooleanField(
        _('Auto-provision users'),
        default=True,
        help_text=_('Automatically create member accounts on first SSO login.'),
    )

    idp_entity_id = models.CharField(_('IdP entity ID'), max_length=500, blank=True)
    idp_x509cert = models.TextField(_('IdP x509 certificate'), blank=True)
    idp_sso_url = models.URLField(_('IdP single sign-on URL'), max_length=500, blank=True)
    idp_sso_binding = models.CharField(
        _('IdP SSO binding'),
        max_length=255,
        default=SAML_BINDING_HTTP_REDIRECT,
    )
    idp_sls_url = models.URLField(_('IdP single logout URL'), max_length=500, blank=True)
    idp_sls_binding = models.CharField(
        _('IdP SLO binding'),
        max_length=255,
        default=SAML_BINDING_HTTP_REDIRECT,
    )

    sp_entity_id = models.CharField(_('SP entity ID'), max_length=500, blank=True)
    sp_name_id_format = models.CharField(
        _('SP NameID format'),
        max_length=255,
        choices=SAML_NAME_ID_FORMATS,
        default='urn:oasis:names:tc:SAML:2.0:nameid-format:string',
    )
    sp_acs_url = models.URLField(
        _('SP assertion consumer URL'),
        max_length=500,
        blank=True,
        help_text=_('Typically https://your-domain/token/login/'),
    )
    sp_acs_binding = models.CharField(
        _('SP ACS binding'),
        max_length=255,
        default=SAML_BINDING_HTTP_POST,
    )
    sp_sls_url = models.URLField(
        _('SP single logout URL'),
        max_length=500,
        blank=True,
        help_text=_('Typically https://your-domain/token/logout/'),
    )
    sp_sls_binding = models.CharField(
        _('SP SLO binding'),
        max_length=255,
        default=SAML_BINDING_HTTP_REDIRECT,
    )
    sp_x509cert = models.TextField(_('SP x509 certificate'), blank=True)
    sp_private_key = models.TextField(_('SP private key'), blank=True)

    requested_authn_context = models.BooleanField(
        _('Request authentication context'),
        default=False,
        help_text=_('Disable for most Azure AD / Entra ID integrations.'),
    )
    requested_authn_context_comparison = models.CharField(
        _('Requested authentication context comparison'),
        max_length=50,
        blank=True,
    )
    authn_requests_signed = models.BooleanField(_('Sign authentication requests'), default=False)
    want_assertions_signed = models.BooleanField(_('Require signed assertions'), default=False)
    security_overrides = models.JSONField(
        _('Security overrides'),
        blank=True,
        null=True,
        help_text=_('Optional JSON for uncommon python-saml security settings.'),
    )

    class Meta(object):
        verbose_name = _('Single sign-on provider')
        verbose_name_plural = _('Single sign-on providers')

    @property
    def is_configured(self):
        return bool(self.idp_entity_id and self.idp_sso_url and self.sp_entity_id and self.sp_acs_url)

    def to_token_auth_settings(self):
        settings = {
            'backend': self.backend,
            'strict': self.strict,
            'debug': self.debug,
            'assertion_mapping': self.get_assertion_mapping(),
            'idp': {
                'entityId': self.idp_entity_id,
                'singleSignOnService': {
                    'url': self.idp_sso_url,
                    'binding': self.idp_sso_binding,
                },
                'singleLogoutService': {
                    'url': self.idp_sls_url,
                    'binding': self.idp_sls_binding,
                },
                'x509cert': self.idp_x509cert,
            },
            'sp': {
                'entityId': self.sp_entity_id,
                'NameIDFormat': self.sp_name_id_format,
                'assertionConsumerService': {
                    'url': self.sp_acs_url,
                    'binding': self.sp_acs_binding,
                },
                'singleLogoutService': {
                    'url': self.sp_sls_url,
                    'binding': self.sp_sls_binding,
                },
            },
        }

        if self.admin_login:
            settings['admin_login'] = True
        if not self.provision:
            settings['provision'] = False

        security = dict(self.security_overrides or {})
        if 'requestedAuthnContext' not in security:
            security['requestedAuthnContext'] = self.requested_authn_context
        if self.requested_authn_context_comparison:
            security['requestedAuthnContextComparison'] = self.requested_authn_context_comparison
        if self.authn_requests_signed:
            security['authnRequestsSigned'] = True
        if self.want_assertions_signed:
            security['wantAssertionsSigned'] = True
        if security:
            settings['security'] = security

        if self.sp_x509cert:
            settings['sp']['x509cert'] = self.sp_x509cert
        if self.sp_private_key:
            settings['sp']['privateKey'] = self.sp_private_key

        return settings

    def get_assertion_mapping(self):
        mapping = {}
        for assertion_mapping in self.assertion_mappings.all():
            key = assertion_mapping.get_mapping_key()
            if key:
                mapping[key] = assertion_mapping.assertion
        return mapping

    @classmethod
    def from_token_auth_settings(cls, platform_settings, token_auth_settings):
        provider, _created = cls.objects.get_or_create(settings=platform_settings)
        provider.backend = token_auth_settings.get(
            'backend', 'token_auth.auth.saml.SAMLAuthentication'
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
        ).get('binding', SAML_BINDING_HTTP_REDIRECT)
        provider.idp_sls_url = idp.get('singleLogoutService', {}).get('url', '')
        provider.idp_sls_binding = idp.get(
            'singleLogoutService', {}
        ).get('binding', SAML_BINDING_HTTP_REDIRECT)

        sp = token_auth_settings.get('sp', {})
        provider.sp_entity_id = sp.get('entityId', '')
        provider.sp_name_id_format = sp.get(
            'NameIDFormat', 'urn:oasis:names:tc:SAML:2.0:nameid-format:string'
        )
        provider.sp_acs_url = sp.get('assertionConsumerService', {}).get('url', '')
        provider.sp_acs_binding = sp.get(
            'assertionConsumerService', {}
        ).get('binding', SAML_BINDING_HTTP_POST)
        provider.sp_sls_url = sp.get('singleLogoutService', {}).get('url', '')
        provider.sp_sls_binding = sp.get(
            'singleLogoutService', {}
        ).get('binding', SAML_BINDING_HTTP_REDIRECT)
        provider.sp_x509cert = sp.get('x509cert', '')
        provider.sp_private_key = sp.get('privateKey', '')

        security = token_auth_settings.get('security', {})
        requested_authn_context = security.get('requestedAuthnContext', False)
        if isinstance(requested_authn_context, bool):
            provider.requested_authn_context = requested_authn_context
            provider.security_overrides = None
        else:
            provider.requested_authn_context = False
            provider.security_overrides = security

        provider.requested_authn_context_comparison = security.get(
            'requestedAuthnContextComparison', ''
        )
        provider.authn_requests_signed = security.get('authnRequestsSigned', False)
        provider.want_assertions_signed = security.get('wantAssertionsSigned', False)
        provider.save()

        provider.assertion_mappings.all().delete()
        for key, assertion in token_auth_settings.get('assertion_mapping', {}).items():
            mapping_type, segment_type, segment_slug = SingleSignOnAssertionMapping.parse_mapping_key(
                key
            )
            if not mapping_type:
                continue
            SingleSignOnAssertionMapping.objects.create(
                provider=provider,
                mapping_type=mapping_type,
                segment_type=segment_type,
                segment_slug=segment_slug,
                assertion=assertion,
            )

        return provider


class SingleSignOnAssertionMapping(models.Model):
    MAPPING_TYPES = (
        ('email', _('Email')),
        ('first_name', _('First name')),
        ('last_name', _('Last name')),
        ('remote_id', _('Remote ID')),
        ('location_name', _('Location name')),
        ('location_slug', _('Location slug')),
        ('segment', _('Segment')),
    )

    MAPPING_TYPE_KEYS = {
        'email': 'email',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'remote_id': 'remote_id',
        'location_name': 'location.name',
        'location_slug': 'location.slug',
    }

    provider = models.ForeignKey(
        SingleSignOnProvider,
        on_delete=models.CASCADE,
        related_name='assertion_mappings',
    )
    mapping_type = models.CharField(_('Member field'), max_length=50, choices=MAPPING_TYPES)
    segment_type = models.ForeignKey(
        SegmentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_('Required for segment mappings.'),
    )
    segment_slug = models.CharField(
        _('Segment type slug'),
        max_length=100,
        blank=True,
        help_text=_('Used when the segment type is not linked yet.'),
    )
    assertion = models.CharField(_('SAML assertion'), max_length=500)

    class Meta(object):
        verbose_name = _('SSO assertion mapping')
        verbose_name_plural = _('SSO assertion mappings')
        unique_together = (('provider', 'mapping_type', 'segment_type', 'segment_slug'),)

    def get_mapping_key(self):
        if self.mapping_type == 'segment':
            slug = self.segment_type.slug if self.segment_type else self.segment_slug
            return 'segment.{}'.format(slug) if slug else None
        return self.MAPPING_TYPE_KEYS.get(self.mapping_type)

    @classmethod
    def parse_mapping_key(cls, key):
        if key in cls.MAPPING_TYPE_KEYS.values():
            mapping_type = next(
                mapping_type for mapping_type, value in cls.MAPPING_TYPE_KEYS.items()
                if value == key
            )
            return mapping_type, None, ''

        if key.startswith('segment.'):
            slug = key.replace('segment.', '', 1)
            segment_type = SegmentType.objects.filter(slug=slug).first()
            return 'segment', segment_type, slug if not segment_type else ''

        return None, None, ''


class MemberPlatformSettings(TranslatableModel, BasePlatformSettings):
    LOGIN_METHODS = (
        ('SSO', _('Company SSO')),
        ('password', _('Email + password')),
    )

    DISPLAY_MEMBER_OPTIONS = (
        ('full_name', _('Full name')),
        ('first_name', _('First name (members)')),
        ('first_name_strict', _('First name (also activity managers)')),
    )

    REQUIRED_QUESTIONS_OPTIONS = (
        ('login', _('After log in')),
        ('contribution', _('When making a contribution')),
    )

    ACCOUNT_CREATION_RULES = (
        ('anyone', _('Anyone can create an account')),
        ('whitelist', _('Only people with a whitelisted domain can create an account')),
        (
            'whitelist_and_request',
            _('People with a whitelisted domain can create an account; all others can request access')
        ),
    )

    REQUEST_ACCESS_METHODS = (
        ('email', _('People request access by entering their email address')),
        ('instructions', _('People request access by following your instructions')),
    )

    closed = CheckboxField(
        _('Platform access'), default=False,
        inline_label=_('Require log in before accessing the platform'),
        help_text=_('Only logged-in users can view the platform.')
    )
    create_initiatives = models.BooleanField(
        _('create initiatives'), default=True, help_text=_('Members can create initiatives')
    )
    do_good_hours = models.PositiveIntegerField(
        _('Impact hours'),
        null=True, blank=True,
        help_text=_("Leave empty if this feature won't be used.")
    )
    fiscal_month_offset = models.IntegerField(
        _('Fiscal year offset'),
        help_text=_(
            'Set how many months earlier your fiscal year starts compared to January. '
            'For example, if your fiscal year starts in September (which is 4 months before '
            'January), enter 4. This also affects how impact metrics are displayed on the homepage.'
        ),
        default=0)

    reminder_q1 = models.BooleanField(
        _('Reminder Q1'),
        default=False,
    )
    reminder_q2 = models.BooleanField(
        _('Reminder Q2'),
        default=False,
    )
    reminder_q3 = models.BooleanField(
        _('Reminder Q3'),
        default=False,
    )
    reminder_q4 = models.BooleanField(
        _('Reminder Q4'),
        default=False,
    )

    login_methods = MultiSelectField(
        _('login methods'),
        help_text=_(
            'People can use any selected method to sign up or log in. '
            'For social log in options, see the ‘Social log in’ tab.'
        ),
        max_length=100,
        choices=LOGIN_METHODS,
        default=['password']
    )
    confirm_signup = CheckboxField(
        _('verify email on sign up'),
        default=False,
        inline_label=_('Require users to verify their email on sign-up'),
        help_text=_('This rule only applies to the email + password method.'),
    )

    account_creation_rules = CharField(
        _('account creation rules'),
        help_text=_('This rule only applies to the email + password method.'),
        choices=ACCOUNT_CREATION_RULES,
        default='anyone',
    )

    email_domains = ArrayField(
        models.CharField(),
        verbose_name=_('Whitelisted email domains'),
        blank=True, null=True,
        default=list,
    )

    support_groups = ArrayField(
        models.CharField(),
        verbose_name=_('Support login groups'),
        default=default_support_groups,
        help_text=_('Groups that can login in using support accounts'),
    )

    session_only = models.BooleanField(
        _('session only'),
        default=False,
        help_text=_('Limit user session to browser session')
    )

    explicit_terms = models.BooleanField(
        _('Explicit terms'),
        default=False,
        help_text=_('Users have to explicitly accept terms when logging in')
    )

    request_access_method = models.CharField(
        _('request access method'),
        help_text=_('This rule only applies when requesting access is allowed.'),
        choices=REQUEST_ACCESS_METHODS,
        default='email',
    )

    translations = TranslatedFields(
        request_access_instructions=models.CharField(
            _('request access instructions'),
            help_text=_('Explain how people can request access to the platform.'),
            max_length=2000,
            null=True,
            blank=True
        ),
    )

    request_access_email = models.EmailField(
        _('Request access mail to address'),
        help_text=_('Enter the email address where people should send their access request.'),
        null=True,
        blank=True
    )

    request_access_code = models.CharField(
        _('Request access code'),
        help_text=_('With this code people can sign-up without a white-listed email address.'),
        max_length=255,
        null=True,
        blank=True
    )

    required_questions_location = models.CharField(
        _('required questions location'),
        choices=REQUIRED_QUESTIONS_OPTIONS,
        max_length=12,
        default='login',
        help_text=_(
            'When should the user be asked to complete their required profile fields?'
        )
    )

    consent_link = models.CharField(
        _('consent link'),
        default='"https://goodup.com/cookie-policy"',
        help_text=_('Link more information about the platforms cookie policy'),
        max_length=255
    )

    disable_cookie_consent = models.BooleanField(
        _('disable cookie consent'),
        default=False,
        help_text=_(
            'Handle cookie consent externally (e.g. Cookiebot) - (Required when GTM is added.)'
        )
    )

    gtm_code = models.CharField(
        _('gtm code'),
        help_text=_('Adding the GTM script to your platform allows you to manage and deploy third-party tools.'),
        max_length=255,
        blank=True
    )

    background = models.ImageField(
        _('Sign up image'),
        help_text=_('This image will be displayed on the sign up and log in pages.'),
        null=True, blank=True, upload_to='site_content/',
        validators=[
            FileMimetypeValidator(
                allowed_mimetypes=settings.IMAGE_ALLOWED_MIME_TYPES,
            ),
            validate_file_infection
        ]
    )

    translate_user_content = models.BooleanField(
        _('translate user content'),
        help_text=_('Give users the option to translate user generated content.'),
        default=False
    )

    enable_gender = models.BooleanField(
        _('enable gender'),
        default=False,
        help_text=_('Show gender question in profile form')
    )

    enable_birthdate = models.BooleanField(
        _('enable birthday'),
        default=False,
        help_text=_('Show birthdate question in profile form')
    )

    enable_address = models.BooleanField(
        _('email address'),
        default=False,
        help_text=_('Show address question in profile form')
    )

    create_segments = models.BooleanField(
        _('create segments'),
        default=False,
        help_text=_(
            "Create new segments when a user logs in. "
            "Leave unchecked if only priorly specified ones should be used."
        ),
    )
    create_locations = models.BooleanField(
        _('create locations'),
        default=False,
        help_text=_(
            "Create new work locations when a user logs in. "
            "Leave unchecked if only priorly specified ones should be used."
        ),
    )

    require_office = models.BooleanField(
        _('Work location'),
        default=False,
        help_text=_('Require members to enter their work location.')
    )
    require_address = models.BooleanField(
        _('Address'),
        default=False,
        help_text=_('Require members to enter their address.')
    )
    require_phone_number = models.BooleanField(
        _('Phone number'),
        default=False,
        help_text=_('Require members to enter their phone number.')
    )
    require_birthdate = models.BooleanField(
        _('Birthdate'),
        default=False,
        help_text=_('Require members to enter their date of birth.')
    )

    verify_office = models.BooleanField(
        _('Verify SSO data work location'),
        default=False,
        help_text=_('Require members to verify their work location once if it is filled via SSO.')
    )

    display_member_names = models.CharField(
        _('Display member names'),
        choices=DISPLAY_MEMBER_OPTIONS,
        max_length=50,
        default='full_name',
        help_text=_(
            'How names of members will be displayed for visitors and other members.'
            'If first name is selected, then the names of initiators and activity manager '
            'will remain displayed in full and Activity managers and initiators will see '
            'the full names of their participants. And staff members will see all names in full.'
        )
    )

    retention_anonymize = models.PositiveIntegerField(
        _('Anonymise'),
        default=None,
        null=True,
        blank=True,
        help_text=_(
            'Set the number of months after which user data will be anonymised. '
            'Leave the field empty or with ‘0’ if you do not wish to anonymise user data.'
        )

    )

    retention_delete = models.PositiveIntegerField(
        _('Delete'),
        default=None,
        null=True,
        blank=True,
        help_text=_(
            'Set the number of months after which user data will be deleted. '
            'Leave the field empty or with ‘0’ if you do not wish to delete user data.'
        )

    )

    @property
    def fiscal_year_start(self):
        offset = self.fiscal_month_offset
        month_start = (datetime(now().year, 1, 1) + relativedelta(months=offset)).month
        fiscal_year = (now() + relativedelta(months=offset)).replace(
            month=month_start, day=1, hour=0, minute=0, second=0
        )
        if now().month < month_start:
            return fiscal_year - relativedelta(years=1)
        return fiscal_year

    @property
    def fiscal_year_end(self):
        return self.fiscal_year_start + relativedelta(years=1) - timedelta(seconds=1)

    def fiscal_year(self):
        offset = self.fiscal_month_offset
        if (now().month - offset) < 0:
            return (now() - relativedelta(months=offset)).year + 1
        return (now() - relativedelta(months=offset)).year

    class Meta(object):
        verbose_name_plural = _('member platform settings')
        verbose_name = _('member platform settings')


@python_2_unicode_compatible
class Member(BlueBottleBaseUser):
    verified = models.BooleanField(default=False, blank=True, help_text=_('Was verified for voting by recaptcha.'))
    accepted = models.BooleanField(
        _('Accepted'),
        default=True,
        help_text=_('Was approved by platform manager.')
    )
    subscribed = models.BooleanField(
        _('Matching'),
        default=False,
        help_text=_("Monthly overview of activities that match this person's profile")
    )
    receive_reminder_emails = models.BooleanField(
        _('Receive reminder emails'),
        default=True,
        help_text=_("User receives emails reminding them about their do good hours")
    )

    remote_id = models.CharField(_('remote_id'),
                                 max_length=75,
                                 blank=True,
                                 null=True)
    last_logout = models.DateTimeField(_('Last Logout'), blank=True, null=True)

    scim_external_id = models.CharField(
        _('external SCIM id'),
        max_length=75,
        blank=True,
        null=True
    )

    place = models.ForeignKey(Place, null=True, blank=True, on_delete=models.SET_NULL)

    subregion_manager = models.ManyToManyField(
        OfficeSubRegion,
        verbose_name=_("Work location groups managed"),
        help_text=_(
            "Filter this user's view to one or more location groups. Leave empty to show data from all locations."
        ),
        blank=True,
    )

    office_manager = models.ManyToManyField(
        Location,
        verbose_name=_("Work locations managed"),
        help_text=_(
            "Filter this user's view to specific work locations. Leave empty to show data from all locations."
        ),
        blank=True,
    )

    segment_manager = models.ManyToManyField(
        Segment,
        verbose_name=_("Segments managed"),
        help_text=_(
            "Select one or more segments to filter on. "
            "The user will only get updates for activities with the selected segments."
        ),
        blank=True,
    )

    matching_options_set = models.DateTimeField(
        null=True, blank=True, help_text=_('When the user updated their matching preferences.')
    )

    segments = models.ManyToManyField(
        'segments.segment',
        verbose_name=_('Segment'),
        related_name='users',
        blank=True,
        through='members.UserSegment'
    )

    avatar = ImageField(blank=True, null=True)

    terms_accepted = models.BooleanField(
        _('Terms accepted'),
        default=False,
        help_text=_('User has explicitly accepted the terms')
    )

    @classmethod
    def create_by_email(cls, email, **kwargs):
        validate_email(email)
        name, _domain = email.split('@')
        names = name.split('.')
        first_name = names.pop(0)
        last_name = ' '.join(names) or ''
        user = cls.objects.create(
            email=email,
            username=email,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
        )
        return user

    def __init__(self, *args, **kwargs):
        super(Member, self).__init__(*args, **kwargs)

        try:
            self._previous_last_seen = self.last_seen
        except ObjectDoesNotExist:
            self._previous_last_seen = None

    class Analytics(object):
        type = 'member'
        tags = {}
        fields = {
            'user_id': 'id'
        }

        @staticmethod
        def extra_tags(obj, created):
            if created:
                return {'event': 'signup'}
            else:
                # The skip method below is being used to ensure analytics are only
                # triggered if the last_seen field has changed.
                return {'event': 'seen'}

        @staticmethod
        def skip(obj, created):
            # Currently only the signup (created) event is being recorded
            # and when the last_seen changes.
            return False if created or obj.last_seen != obj._previous_last_seen else True

        @staticmethod
        def timestamp(obj, created):
            # This only serves the purpose when we record the member created logs
            # We need to modify this if we ever record member deleted
            if created:
                return obj.date_joined
            else:
                return obj.updated

    @property
    def initials(self):
        initials = ''
        if self.first_name:
            initials += self.first_name[0]
        if self.last_name:
            initials += self.last_name[0]

        return initials

    @property
    def required(self):
        required = []
        for segment_type in SegmentType.objects.filter(required=True).all():
            if not self.segments.filter(
                usersegment__verified=True, segment_type=segment_type
            ).count():
                required.append(f'segment_type.{segment_type.id}')

        platform_settings = MemberPlatformSettings.load()

        if platform_settings.require_office and (
            not self.location or
            (platform_settings.verify_office and not self.location_verified)
        ):
            required.append('location')

        for attr in ['birthdate', 'phone_number']:
            if getattr(platform_settings, f'require_{attr}') and not getattr(self, attr):
                required.append(attr)

        if platform_settings.require_address and not (self.place and self.place.complete):
            required.append('address')

        return required

    def __str__(self):
        return self.full_name

    def get_hours(self, status):
        from ..time_based.models import TimeContribution
        platform_settings = MemberPlatformSettings.load()
        year_start = platform_settings.fiscal_year_start
        year_end = platform_settings.fiscal_year_end
        hours = TimeContribution.objects.filter(
            contributor__user=self,
            status=status,
            start__gte=year_start,
            start__lte=year_end
        ).aggregate(hours=Sum('value'))['hours']
        if hours:
            return hours.seconds / 3600 + hours.days * 24
        return 0.0

    @property
    def hours_spent(self):
        return self.get_hours('succeeded')

    @property
    def hours_planned(self):
        return self.get_hours('new')


class UserSegment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    segment = models.ForeignKey('segments.segment', on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)


class UserActivity(models.Model):
    user = models.ForeignKey(Member, null=True, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=200, null=True, blank=True)

    class Meta(object):
        verbose_name = _('User activity')
        verbose_name_plural = _('User activities')
        ordering = ['-created']


from . import signals  # noqa
