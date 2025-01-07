import functools
from builtins import object

from adminfilters.multiselect import UnionFieldListFilter
from adminsortable.admin import NonSortableParentAdmin
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.db import connection
from django.db import models
from django.db.models import Q, Count
from django.forms import BaseInlineFormSet
from django.forms.widgets import Select
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.template import loader
from django.template.response import TemplateResponse
from django.urls import reverse, NoReverseMatch, re_path
from django.utils.html import format_html
from django.utils.http import int_to_base36
from django.utils.translation import gettext_lazy as _
from django_admin_inline_paginator.admin import TabularInlinePaginated
from rest_framework.authtoken.models import Token

from bluebottle.bb_accounts.utils import send_welcome_mail
from bluebottle.bb_follow.models import Follow
from bluebottle.bluebottle_dashboard.decorators import confirmation_form
from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url
from bluebottle.collect.models import CollectContributor
from bluebottle.deeds.models import DeedParticipant
from bluebottle.funding.models import Donor, PaymentProvider
from bluebottle.funding_pledge.models import PledgePaymentProvider
from bluebottle.geo.models import Location
from bluebottle.initiatives.models import Initiative
from bluebottle.members.forms import (
    LoginAsConfirmationForm,
    SendWelcomeMailConfirmationForm,
    SendPasswordResetMailConfirmationForm
)
from bluebottle.members.models import (
    MemberPlatformSettings,
    UserActivity,
)
from bluebottle.notifications.models import Message
from bluebottle.segments.admin import SegmentAdminFormMetaClass
from bluebottle.segments.models import SegmentType
from bluebottle.time_based.models import (
    DateParticipant,
    PeriodicParticipant,
    DeadlineParticipant,
    ScheduleParticipant,
    TeamScheduleParticipant,
)
from bluebottle.utils.admin import (
    export_as_csv_action,
    BasePlatformSettingsAdmin,
    admin_info_box,
)
from bluebottle.utils.email_backend import send_mail
from bluebottle.utils.widgets import SecureAdminURLFieldWidget
from .models import Member, UserSegment
from ..offices.admin import RegionManagerAdminMixin
from ..offices.models import OfficeSubRegion


class MemberForm(forms.ModelForm, metaclass=SegmentAdminFormMetaClass):
    def __init__(self, data=None, files=None, current_user=None, *args, **kwargs):
        self.current_user = current_user
        super(MemberForm, self).__init__(data, files, *args, **kwargs)

        if self.current_user.is_superuser:
            # Superusers can assign every group to a user
            group_queryset = Group.objects.all()
        else:
            # Normal staff users can only choose groups that they belong to.
            group_queryset = Group.objects.filter(
                pk__in=self.current_user.groups.all().only('pk')
            )

        self.fields['groups'] = forms.ModelMultipleChoiceField(
            queryset=group_queryset,
            required=False,
            initial=Group.objects.filter(name='Authenticated')
        )

    class Meta(object):
        model = Member
        # Mind you these fields are also set in MemberAdmin.add_fieldsets
        fields = '__all__'


class MemberCreationForm(MemberForm):
    """
    A form that creates a member.
    """
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
    }
    email = forms.EmailField(label=_("Email address"), max_length=254,
                             help_text=_("A valid, unique email address."))

    is_active = forms.BooleanField(label=_("Is active"), initial=True)

    def clean_email(self):
        # Since BlueBottleUser.email is unique, this check is redundant
        # but it sets a nicer error message than the ORM.
        email = self.cleaned_data["email"]
        try:
            Member._default_manager.get(email=email)
        except Member.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(MemberCreationForm, self).save(commit=False)
        if commit:
            user.save()
        return user


class MemberPlatformSettingsAdmin(BasePlatformSettingsAdmin, NonSortableParentAdmin):

    def reminder_info(self, obj):
        return admin_info_box(
            _('Quarterly emails will only be sent at the beginning of each '
              'quarter if the impact hours are set. Users will only receive '
              'the emails if they have not spent all the set hours.')
        )

    def impact_hours_info(self, obj):
        return admin_info_box(
            _('The impact hours feature will show the amount of hours '
              'users are encouraged to spend making an impact each year.')
        )

    fieldsets = (
        (
            _('Login'),
            {
                'fields': (
                    'closed', 'confirm_signup', 'login_methods', 'email_domain',
                    'background',
                )
            }
        ),

        (
            _('Profile'),
            {
                'fields': (
                    'enable_gender', 'enable_birthdate', 'enable_segments',
                    'enable_address', 'create_segments'
                )
            }
        ),
        (
            _('Privacy'),
            {
                'fields': (
                    'session_only',
                    'consent_link',
                    'disable_cookie_consent',
                    'anonymization_age',
                    'display_member_names',
                    'gtm_code',
                )
            }
        ),
        (
            _('Impact hours'),
            {
                'fields': (
                    'impact_hours_info',
                    'do_good_hours',
                    'fiscal_month_offset',
                    'reminder_info',
                    'reminder_q1',
                    'reminder_q2',
                    'reminder_q3',
                    'reminder_q4',
                ),
            }
        ),
        (
            _('Initiatives'),
            {
                'fields': (
                    'create_initiatives',
                ),
            }
        ),
        (
            _('User data'),
            {
                'description': _('User data can be anonymised and/or deleted after a set number of months from '
                                 'the time it was created to comply with company policies and local laws. User '
                                 'data includes names, contributions and wall posts. Please contact the support '
                                 'team at GoodUp for more information.'),
                'fields': (
                    'retention_anonymize',
                    'retention_delete'
                )
            }
        )
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = self.fieldsets
        required_fields = [
            'require_birthdate',
            'require_address',
            'require_phone_number'
        ]

        if obj.closed:
            required_fields.insert(0, 'required_questions_location')

        if Location.objects.count():
            required_fields.append('require_office')
            required_fields.append('verify_office')

        if SegmentType.objects.count():
            required_fields.append('segment_types')

        if len(required_fields):
            if obj.closed:
                description = _('Members are required to fill out the fields listed '
                                'below after log in or when contributing to an activity.')
            else:
                description = _('Members are required to fill out the fields listed '
                                'below when contributing to an activity.')
            fieldsets += (
                (
                    _('Required fields'),
                    {
                        'description': description,
                        'fields': required_fields
                    }
                ),
            )

        return fieldsets

    readonly_fields = ('segment_types', 'reminder_info', 'impact_hours_info')

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = super(MemberPlatformSettingsAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            read_only_fields += ('retention_anonymize', 'retention_delete')

        if request.user.region_manager and not request.user.is_superuser:
            read_only_fields += ("region_manager",)

        return read_only_fields

    def segment_types(self, obj):
        template = loader.get_template('segments/admin/required_segment_types.html')
        context = {
            'required': SegmentType.objects.filter(required=True).all(),
            'link': reverse('admin:segments_segmenttype_changelist')
        }
        return template.render(context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        Show confirmation page if retention params change
        """

        obj = MemberPlatformSettings.load()

        if object_id and request.method == 'POST' and not request.POST.get('post', False):
            model_form = self.get_form(request, obj)
            form = model_form(request.POST, request.FILES, instance=obj)

            if 'confirm' in request.POST and request.POST['confirm']:
                if form.is_valid():
                    form.save(commit=False)
                    return HttpResponseRedirect(reverse('admin:members_memberplatformsettings'))

            data = request.POST
            if (
                    data['retention_anonymize'] and str(obj.retention_anonymize) != data['retention_anonymize']
            ) or (
                    data['retention_delete'] and str(obj.retention_delete) != data['retention_delete']
            ):
                context = dict(
                    obj=obj,
                    title=_('Are you sure?'),
                    post=request.POST,
                    opts=self.model._meta,
                    media=self.media,
                )
                return TemplateResponse(
                    request, "admin/members/set_retention_confirmation.html", context
                )

        return super(MemberPlatformSettingsAdmin, self).changeform_view(request, object_id, form_url, extra_context)


admin.site.register(MemberPlatformSettings, MemberPlatformSettingsAdmin)


class SegmentSelect(Select):
    template_name = 'widgets/segment-select.html'

    def __init__(self, verified):
        self.verified = verified
        super().__init__()

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['verified'] = self.verified
        return context


class MemberChangeForm(MemberForm):
    """
    Change Member form
    """

    email = forms.EmailField(label=_("email address"), max_length=254,
                             help_text=_("A valid, unique email address."))

    class Meta(object):
        model = Member
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(MemberChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

        if connection.tenant.schema_name != 'public':
            for segment_type in SegmentType.objects.all():
                user_segment = UserSegment.objects.filter(
                    member=self.instance, segment__segment_type=segment_type
                ).first()

                self.fields[segment_type.field_name] = forms.ModelChoiceField(
                    required=False,
                    label=segment_type.name,
                    queryset=segment_type.segments,
                    widget=SegmentSelect(verified=user_segment.verified if user_segment else None)
                )
                self.initial[segment_type.field_name] = user_segment.segment if user_segment else None

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

    def save(self, commit=True):
        member = super(MemberChangeForm, self).save(commit=commit)
        segments = []
        for segment_type in SegmentType.objects.all():
            segment = self.cleaned_data.get(segment_type.field_name, None)
            if segment:
                segments.append(segment)
        member.segments.set(segments)
        return member


class LimitModelFormset(BaseInlineFormSet):
    """ Base Inline formset to limit inline Model query results. """
    LIMIT = 20

    def __init__(self, *args, **kwargs):
        super(LimitModelFormset, self).__init__(*args, **kwargs)
        _kwargs = {self.fk.name: kwargs['instance']}
        self.queryset = kwargs['queryset'].filter(**_kwargs).order_by('-id')[:self.LIMIT]


class UserActivityInline(admin.TabularInline):
    readonly_fields = ['created', 'user', 'path']
    extra = 0
    model = UserActivity
    can_delete = False

    formset = LimitModelFormset

    def has_add_permission(self, request, obj=None):
        return False


class SortedUnionFieldListFilter(UnionFieldListFilter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_choices = sorted(self.lookup_choices, key=lambda a: a[1].lower())


class MemberMessagesInline(TabularInlinePaginated):
    model = Message
    per_page = 20
    ordering = ('-sent',)
    readonly_fields = [
        'sent', 'template', 'subject', 'content_type', 'related'
    ]
    fields = readonly_fields

    def related(self, obj):
        url = f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change"
        if not obj.content_object:
            return format_html('{}<br><i>{}</i>', obj.content_type, _('Deleted'))
        try:
            return format_html(
                u"<a href='{}'>{}</a>",
                str(reverse(url, args=(obj.object_id,))), obj.content_object or obj.content_type or 'Related object'
            )
        except NoReverseMatch:
            return obj.content_object or 'Related object'


class MemberAdmin(RegionManagerAdminMixin, UserAdmin):
    raw_id_fields = ('partner_organization', 'place', 'location', 'avatar')
    date_hierarchy = 'date_joined'

    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    def get_form(self, request, *args, **kwargs):
        Form = super(MemberAdmin, self).get_form(request, *args, **kwargs)
        return functools.partial(Form, current_user=request.user)

    permission_fields = [
        'is_active',
        'is_staff',
        'is_superuser',
        'groups',
        'is_co_financer',
        'can_pledge',
        'verified',
        'kyc'
    ]

    def get_permission_fields(self, request, obj=None):
        fields = self.permission_fields.copy()
        if OfficeSubRegion.objects.count():
            fields.insert(4, 'region_manager')
        return fields

    def get_fieldsets(self, request, obj=None):
        if not obj:
            fieldsets = (
                (
                    None, {
                        'classes': ('wide',),
                        'fields': [
                            'first_name', 'last_name', 'email', 'is_active',
                            'is_staff', 'groups'
                        ]
                    }
                ),
            )
        else:
            fieldsets = [
                [
                    _("Main"),
                    {
                        'fields': [
                            'email',
                            'remote_id',
                            'username',
                            'first_name',
                            'last_name',
                            'phone_number',
                            'login_as_link',
                            'reset_password',
                            'resend_welcome_link',
                            'last_login',
                            'date_joined',
                            'deleted',
                            'partner_organization',
                            'primary_language',
                        ]
                    }
                ],
                [
                    _("Profile"),
                    {
                        'fields':
                            [
                                'avatar',
                                'about_me',
                                'campaign_notifications',
                            ]

                    }
                ],
                [
                    _('Permissions'),
                    {'fields': self.get_permission_fields(request, obj)}
                ],
                [
                    _('Engagement'),
                    {
                        'fields': self.get_impact_fields(obj)

                    }
                ],
                [
                    _('Search'),
                    {
                        'fields':
                            [
                                'matching_options_set',
                                'search_distance', 'any_search_distance', 'exclude_online',
                                'place', 'favourite_themes', 'skills', 'subscribed',
                            ]
                    }
                ],
            ]

            if Location.objects.count():
                fieldsets[1][1]['fields'].append('location')

            member_settings = MemberPlatformSettings.load()

            if member_settings.enable_gender:
                fieldsets[0][1]['fields'].append('gender')
            if member_settings.enable_birthdate:
                fieldsets[0][1]['fields'].append('birthdate')

            if not PaymentProvider.objects.filter(Q(instance_of=PledgePaymentProvider)).count():
                fieldsets[2][1]['fields'].remove('can_pledge')

            if obj and (obj.is_staff or obj.is_superuser):
                fieldsets[1][1]['fields'].append('submitted_initiative_notifications')

            if SegmentType.objects.count():
                extra = (
                    _('Segments'), {
                        'fields': [
                            segment_type.field_name
                            for segment_type in SegmentType.objects.all()
                        ]
                    }
                )

                fieldsets.insert(2, extra)

        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [
            "date_joined",
            "last_login",
            "updated",
            "deleted",
            "login_as_link",
            "reset_password",
            "resend_welcome_link",
            "initiatives",
            "deadline_activities",
            "periodic_activities",
            "schedule_activities",
            "team_schedule_activities",
            "date_activities",
            "funding",
            "deeds",
            "collect",
            "kyc",
            "hours_spent",
            "hours_planned",
            "all_contributions",
            "data_retention_info",
        ]

        user_groups = request.user.groups.all()

        if obj and hasattr(obj, 'groups') and not request.user.is_superuser:
            for group in obj.groups.all():
                if group not in user_groups:
                    readonly_fields.append('email')

        if not request.user.is_superuser:
            if obj and obj.is_superuser:
                readonly_fields.append('email')

            readonly_fields.append('is_superuser')

        return readonly_fields

    def get_impact_fields(self, obj):
        fields = [
            "all_contributions",
            "hours_spent",
            "hours_planned",
            "initiatives",
            "date_activities",
            "periodic_activities",
            "deadline_activities",
            "schedule_activities",
            "team_schedule_activities",
            "funding",
            "deeds",
            "collect",
        ]
        member_settings = MemberPlatformSettings.load()
        if member_settings.retention_delete or member_settings.retention_anonymize:
            fields.insert(0, 'data_retention_info')

        return fields

    def data_retention_info(self, obj):
        member_settings = MemberPlatformSettings.load()
        months = member_settings.retention_anonymize or member_settings.retention_delete
        return admin_info_box(
            _('Only data from the last {months} months is shown.').format(months=months)
        )

    def hours_spent(self, obj):
        return obj.hours_spent

    hours_spent.short_description = _("Hours spent this year")

    def hours_planned(self, obj):
        return obj.hours_planned

    hours_planned.short_description = _("Hours planned this year")

    def all_contributions(self, obj):
        url = reverse('admin:activities_contribution_changelist') + f'?contributor__user_id={obj.id}'
        return format_html('<a href={}>{}</a>', url, _("Show all contributions"))

    all_contributions.short_description = _("All contributions")

    export_fields = (
        ('email', 'email'),
        ('phone_number', 'phone number'),
        ('remote_id', 'remote id'),
        ('first_name', 'first name'),
        ('last_name', 'last name'),
        ('date_joined', 'date joined'),

        ('is_initiator', 'is initiator'),
        ('is_supporter', 'is supporter'),
        ('is_volunteer', 'is volunteer'),
        ('amount_donated', 'amount donated'),
        ('time_spent', 'time spent'),
        ('subscribed', 'subscribed to matching projects'),
    )

    def get_export_fields(self):
        fields = self.export_fields
        member_settings = MemberPlatformSettings.load()
        if member_settings.enable_gender:
            fields += (('gender', 'gender'),)
        if member_settings.enable_birthdate:
            fields += (('birthdate', 'birthdate'),)
        if member_settings.enable_address:
            fields += (('place__street', 'street'),)
            fields += (('place__street_number', 'street_number'),)
            fields += (('place__locality', 'city'),)
            fields += (('place__postal_code', 'postal_code'),)
            fields += (('place__country__name', 'country'),)
        return fields

    def get_actions(self, request):
        self.actions = (export_as_csv_action(fields=self.get_export_fields()),)

        return super(MemberAdmin, self).get_actions(request)

    form = MemberChangeForm
    add_form = MemberCreationForm

    list_filter = (
        'is_active',
        'newsletter',
        ('favourite_themes', SortedUnionFieldListFilter),
        ('skills', SortedUnionFieldListFilter),
        ('groups', UnionFieldListFilter)
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff',
                    'date_joined', 'is_active', 'login_as_link')
    ordering = ('-date_joined', 'email',)

    inlines = (UserActivityInline, MemberMessagesInline)

    def initiatives(self, obj):
        initiatives = []
        initiative_url = reverse('admin:initiatives_initiative_changelist')
        for field in ['owner', 'reviewer', 'promoter', 'activity_managers']:
            if Initiative.objects.filter(status__in=['draft', 'submitted', 'needs_work'], **{field: obj}).count():
                link = initiative_url + '?{}__id={}'.format(field, obj.id)
                initiatives.append(format_html(
                    '<a href="{}">{}</a> draft {}',
                    link,
                    Initiative.objects.filter(status__in=['draft', 'submitted', 'needs_work'], **{field: obj}).count(),
                    field,
                ))
            if Initiative.objects.filter(status='approved', **{field: obj}).count():
                link = initiative_url + '?{}__id={}'.format(field, obj.id)
                initiatives.append(format_html(
                    '<a href="{}">{}</a> open {}',
                    link,
                    Initiative.objects.filter(status='approved', **{field: obj}).count(),
                    field,
                ))
        if len(initiatives):
            return format_html('<ul>{}</ul>', format_html('<br/>'.join(initiatives)))
        return _('None')

    initiatives.short_description = _('Initiatives')

    def get_stats(self, obj, contributor_model):
        applicants = []
        applicant_url = reverse(
            f"admin:{contributor_model._meta.app_label}_{contributor_model._meta.model_name}_changelist"
        )
        stats = (
            contributor_model.objects.filter(user=obj)
            .values("status")
            .annotate(count=Count("status"))
        )
        for stat in stats:
            link = applicant_url + "?user_id={}&status={}".format(
                obj.id, stat["status"]
            )
            applicants.append(
                format_html(
                    '<a href="{}">{}</a> {}',
                    link,
                    stat["count"],
                    stat["status"],
                )
            )
        if len(applicants):
            return format_html("<ul>{}</ul>", format_html("<br/>".join(applicants)))
        return format_html("<i>{}</i>", _("None"))

    def date_activities(self, obj):
        return self.get_stats(obj, DateParticipant)

    date_activities.short_description = _('Activity on a date')

    def periodic_activities(self, obj):
        return self.get_stats(obj, PeriodicParticipant)

    periodic_activities.short_description = _("Recurring activity")

    def deadline_activities(self, obj):
        return self.get_stats(obj, DeadlineParticipant)

    periodic_activities.short_description = _("Flexible activity")

    def schedule_activities(self, obj):
        return self.get_stats(obj, ScheduleParticipant)

    schedule_activities.short_description = _("Schedule activity")

    def team_schedule_activities(self, obj):
        return self.get_stats(obj, TeamScheduleParticipant)

    team_schedule_activities.short_description = _("Team schedule activity")

    def funding(self, obj):
        donations = []
        donation_url = reverse('admin:funding_donor_changelist')
        if Donor.objects.filter(status='succeeded', user=obj).count():
            link = donation_url + '?user_id={}'.format(obj.id)
            donations.append(format_html(
                '<a href="{}">{}</a> donations',
                link,
                Donor.objects.filter(status='succeeded', user=obj).count(),
            ))
        return format_html('<br/>'.join(donations)) or _('None')

    funding.short_description = _('Funding donations')

    def deeds(self, obj):
        return self.get_stats(obj, DeedParticipant)

    deeds.short_description = _('Deed participation')

    def collect(self, obj):
        return self.get_stats(obj, CollectContributor)

    collect.short_description = _('Collect contributor')

    def following(self, obj):
        url = reverse('admin:bb_follow_follow_changelist')
        follow_count = Follow.objects.filter(user=obj).count()
        return format_html('<a href="{}?user_id={}">{} objects</a>', url, obj.id, follow_count)

    following.short_description = _('Following')

    def reset_password(self, obj):
        reset_mail_url = reverse('admin:auth_user_password_reset_mail', kwargs={'pk': obj.id})
        properties.set_tenant(connection.tenant)

        return format_html(
            "<a href='{}'>{}</a>",
            reset_mail_url, _("Send reset password mail")
        )

    def resend_welcome_link(self, obj):
        welcome_mail_url = reverse('admin:auth_user_resend_welcome_mail', kwargs={'pk': obj.id})
        return format_html(
            "<a href='{}'>{}</a>",
            welcome_mail_url, _("Resend welcome email"),
        )

    def kyc(self, obj):
        if not obj.funding_payout_account.count():
            return '-'
        kyc_url = reverse('admin:funding_payoutaccount_changelist') + '?owner__id__exact={}'.format(obj.id)
        return format_html(
            "<a href='{}'>{} {}</a>",
            kyc_url,
            obj.funding_payout_account.count(),
            _("accounts")
        )

    kyc.short_description = _("KYC accounts")

    def get_inline_instances(self, request, obj=None):
        """ Override get_inline_instances so that the add form does not show inlines """
        if not obj:
            return []
        return super(MemberAdmin, self).get_inline_instances(request, obj)

    def get_urls(self):
        urls = super(MemberAdmin, self).get_urls()

        extra_urls = [
            re_path(
                r'^login-as/(?P<pk>\d+)/$',
                self.admin_site.admin_view(self.login_as),
                name='members_member_login_as'
            ),
            re_path(
                r'^password-reset/(?P<pk>\d+)/$',
                self.send_password_reset_mail,
                name='auth_user_password_reset_mail'
            ),
            re_path(
                r'^resend_welcome_email/(?P<pk>\d+)/$',
                self.resend_welcome_email,
                name='auth_user_resend_welcome_mail'
            )
        ]
        return extra_urls + urls

    @confirmation_form(
        SendPasswordResetMailConfirmationForm,
        Member,
        'admin/members/password_reset.html'
    )
    def send_password_reset_mail(self, request, user):
        if not request.user.has_perm('members.change_member'):
            return HttpResponseForbidden('Not allowed to change user')

        context = {
            'email': user.email,
            'site': tenant_url(),
            'site_name': tenant_url(),
            'uid': int_to_base36(user.pk),
            'user': user,
            'token': default_token_generator.make_token(user),
        }
        subject = loader.render_to_string('bb_accounts/password_reset_subject.txt', context)
        subject = ''.join(subject.splitlines())
        send_mail(
            template_name='bb_accounts/password_reset_email',
            to=user,
            subject=subject,
            **context
        )
        message = _('User {name} will receive an email to reset password.').format(name=user.full_name)
        self.message_user(request, message)
        return HttpResponseRedirect(reverse('admin:members_member_change', args=(user.id,)))

    @confirmation_form(
        SendWelcomeMailConfirmationForm,
        Member,
        'admin/members/resend_welcome_mail.html'
    )
    def resend_welcome_email(self, request, user):
        if not request.user.has_perm('members.change_member'):
            return HttpResponseForbidden('Not allowed to change user')

        send_welcome_mail(user)

        message = _('User {name} will receive an welcome email.').format(name=user.full_name)
        self.message_user(request, message)

        return HttpResponseRedirect(reverse('admin:members_member_change', args=(user.id,)))

    @confirmation_form(
        LoginAsConfirmationForm,
        Member,
        'admin/members/login_as.html'
    )
    def login_as(self, request, user):
        template = loader.get_template('utils/login_with.html')
        context = {'token': user.get_jwt_token(), 'link': '/'}
        response = HttpResponse(template.render(context, request), content_type='text/html')
        response['cache-control'] = "no-store, no-cache, private"
        return response

    def login_as_link(self, obj):
        url = reverse('admin:members_member_login_as', args=(obj.pk,))
        return format_html(
            u"<a target='_blank' href='{}'>{}</a>",
            url, _('Login as user')
        )

    login_as_link.short_description = _('Login as')

    def has_delete_permission(self, request, obj=None):
        if obj and obj.contributor_set.exclude(status__in=['deleted', 'failed']).count() == 0:
            return True
        return False


admin.site.register(Member, MemberAdmin)


class NewGroupChangeForm(forms.ModelForm):
    pass


class GroupsAdmin(GroupAdmin):
    list_display = ["name", ]
    form = NewGroupChangeForm

    class Media(object):
        css = {
            'all': ('css/admin/permissions-table.css',)
        }

    class Meta(object):
        model = Group


admin.site.unregister(Group)
admin.site.register(Group, GroupsAdmin)


class TokenAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    readonly_fields = ('key',)
    fields = ('user', 'key')


admin.site.register(Token, TokenAdmin)
