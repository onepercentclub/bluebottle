import functools
import six
from adminfilters.multiselect import UnionFieldListFilter
from adminsortable.admin import SortableTabularInline, NonSortableParentAdmin
from django.db import models
from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.core.urlresolvers import reverse
from django.db import connection
from django.forms.models import ModelFormMetaclass
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.template import loader
from django.utils.html import format_html
from django.utils.http import int_to_base36
from django.utils.translation import ugettext_lazy as _
from permissions_widget.forms import PermissionSelectMultipleField

from bluebottle.bb_accounts.models import UserAddress
from bluebottle.bb_accounts.utils import send_welcome_mail
from bluebottle.bb_follow.models import Follow
from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url
from bluebottle.donations.models import Donation
from bluebottle.geo.models import Location
from bluebottle.members.models import CustomMemberFieldSettings, CustomMemberField, MemberPlatformSettings
from bluebottle.projects.models import Project
from bluebottle.tasks.models import Task
from bluebottle.utils.admin import export_as_csv_action, BasePlatformSettingsAdmin

from bluebottle.utils.email_backend import send_mail
from bluebottle.utils.widgets import SecureAdminURLFieldWidget
from .models import Member


class MemberForm(forms.ModelForm):
    def __init__(self, data=None, files=None, current_user=None, *args, **kwargs):
        self.current_user = current_user
        super(MemberForm, self).__init__(data, files, *args, **kwargs)

        if self.current_user.is_superuser:
            # Super users can assign every group to a user
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

    class Meta:
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


class CustomMemberFieldSettingsInline(SortableTabularInline):
    model = CustomMemberFieldSettings
    readonly_fields = ('slug',)
    extra = 0


class MemberPlatformSettingsAdmin(BasePlatformSettingsAdmin, NonSortableParentAdmin):

    inlines = [
        CustomMemberFieldSettingsInline
    ]


admin.site.register(MemberPlatformSettings, MemberPlatformSettingsAdmin)


class CustomAdminFormMetaClass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if connection.tenant.schema_name != 'public':
            for field in CustomMemberFieldSettings.objects.all():
                attrs[field.slug] = forms.CharField(required=False,
                                                    label=field.name,
                                                    help_text=field.description)

        return super(CustomAdminFormMetaClass, cls).__new__(cls, name, bases, attrs)


class MemberChangeForm(six.with_metaclass(CustomAdminFormMetaClass, MemberForm)):
    """
    Change Member form
    """

    email = forms.EmailField(label=_("email address"), max_length=254,
                             help_text=_("A valid, unique email address."))

    class Meta:
        model = Member
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(MemberChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

        if connection.tenant.schema_name != 'public':
            for field in CustomMemberFieldSettings.objects.all():
                self.fields[field.slug] = forms.CharField(required=False,
                                                          label=field.name,
                                                          help_text=field.description)
                if CustomMemberField.objects.filter(member=self.instance, field=field).exists():
                    value = CustomMemberField.objects.filter(member=self.instance, field=field).get().value
                    self.initial[field.slug] = value

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

    def save(self, commit=True):
        member = super(MemberChangeForm, self).save(commit=commit)
        for field in CustomMemberFieldSettings.objects.all():
            extra, created = CustomMemberField.objects.get_or_create(
                member=member,
                field=field
            )
            extra.value = self.cleaned_data.get(field.slug, None)
            extra.save()
        return member


class UserAddressInline(admin.StackedInline):
    model = UserAddress

    def has_delete_permission(self, request, obj=None):
        return False


class MemberAdmin(UserAdmin):
    raw_id_fields = ('partner_organization', )

    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }

    def get_form(self, request, *args, **kwargs):
        Form = super(MemberAdmin, self).get_form(request, *args, **kwargs)
        return functools.partial(Form, current_user=request.user)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            fieldsets = ((
                None, {
                    'classes': ('wide', ),
                    'fields': [
                        'first_name', 'last_name', 'email', 'is_active',
                        'is_staff', 'groups'
                    ]
                }
            ), )
        else:
            fieldsets = [
                [
                    _("Main"),
                    {
                        'fields': [
                            'email',
                            'remote_id',
                            'first_name',
                            'last_name',
                            'phone_number',
                            'reset_password',
                            'resend_welcome_link',
                            'last_login',
                            'date_joined',
                            'deleted',
                            'is_co_financer',
                            'can_pledge',
                            'partner_organization',
                            'campaign_notifications',
                            'newsletter',
                            'primary_language',
                        ]
                    }
                ],
                [
                    _("Profile"),
                    {
                        'fields':
                        ['picture', 'about_me', 'favourite_themes', 'skills']
                    }
                ],
                [
                    _('Permissions'),
                    {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups']}
                ],
                [
                    _('Engagement'),
                    {
                        'fields':
                        ['projects_managed', 'tasks', 'donations', 'following']
                    }
                ],
            ]

            if Location.objects.count():
                fieldsets[1][1]['fields'].append('location')

            if 'Pledge' not in (
                item['name'] for item in properties.PAYMENT_METHODS
            ):
                fieldsets[0][1]['fields'].remove('can_pledge')

            if CustomMemberFieldSettings.objects.count():
                extra = (
                    _('Extra fields'), {
                        'fields': [
                            field.slug
                            for field in CustomMemberFieldSettings.objects.all()
                        ]
                    }
                )

                fieldsets.append(extra)

        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [
            'date_joined', 'last_login',
            'updated', 'deleted', 'login_as_user',
            'reset_password', 'resend_welcome_link',
            'projects_managed', 'tasks', 'donations', 'following'
        ]

        user_groups = request.user.groups.all()

        if obj and hasattr(obj.groups):
            for group in obj.groups.all():
                if group not in user_groups:
                    readonly_fields.append('email')

        if not request.user.is_superuser:
            readonly_fields.append('is_superuser')

        return readonly_fields

    export_fields = (
        ('username', 'username'),
        ('email', 'email'),
        ('remote_id', 'remote_id'),
        ('first_name', 'first_name'),
        ('last_name', 'last name'),
        ('date_joined', 'date joined'),
        ('is_initiator', 'is initiator'),
        ('is_supporter', 'is supporter'),
        ('amount_donated', 'amount donated'),
        ('is_volunteer', 'is volunteer'),
        ('time_spent', 'time spent'),
    )

    actions = (export_as_csv_action(fields=export_fields),)

    form = MemberChangeForm
    add_form = MemberCreationForm

    list_filter = (
        'is_active',
        'newsletter',
        ('favourite_themes', UnionFieldListFilter),
        ('skills', UnionFieldListFilter),
        ('groups', UnionFieldListFilter)
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff',
                    'date_joined', 'is_active', 'login_as_user')
    ordering = ('-date_joined', 'email',)

    inlines = (UserAddressInline, )

    def projects_managed(self, obj):
        url = reverse('admin:projects_project_changelist')
        completed = Project.objects.filter(owner=obj, status__slug__in=['done-complete', 'done-incomplete']).count()
        campaign = Project.objects.filter(owner=obj, status__slug__in=['campaign', 'voting-running']).count()
        submitted = Project.objects.filter(owner=obj, status__slug='plan-submitted').count()
        plan = Project.objects.filter(owner=obj, status__slug__in=['plan-new', 'plan-needs-work']).count()
        links = []
        if completed:
            links.append('<a href="{}?owner={}&status_filter=8%2C9">{} {}</a>'.format(
                url, obj.id, completed, _('completed')
            ))
        if campaign:
            links.append('<a href="{}?owner={}&status_filter=11%2C5">{} {}</a>'.format(
                url, obj.id, campaign, _('campaigning')
            ))
        if plan:
            links.append('<a href="{}?owner={}&status_filter=1%2C3">{} {}</a>'.format(
                url, obj.id, plan, _('plan')
            ))
        if submitted:
            links.append('<a href="{}?owner={}&status_filter=2">{} {}</a>'.format(
                url, obj.id, submitted, _('submitted')
            ))
        return format_html(', '.join(links) or _('None'))
    projects_managed.short_description = _('Projects Managed')

    def tasks(self, obj):
        url = reverse('admin:tasks_task_changelist')
        owner = Task.objects.filter(author=obj, status__in=['open', 'full', 'running', 'realised']).count()
        applied = Task.objects.filter(members__member=obj, members__status__in=['applied', 'accepted']).count()
        realized = Task.objects.filter(members__member=obj, members__status__in=['realized']).count()
        links = []
        if owner:
            links.append('<a href="{}?author={}">{} {}</a>'.format(
                url, obj.id, owner, _('created')
            ))
        if applied:
            links.append(
                '<a href="{}?members__member_id={}&members__status[]=applied'
                '&members__status[]=accepted">{} {}</a>'.format(url, obj.id, applied, _('applied'))
            )
        if realized:
            links.append('<a href="{}?members__member_id={}">{} {}</a>'.format(
                url, obj.id, realized, _('realised')
            ))
        return format_html(', '.join(links) or _('None'))
    tasks.short_description = _('Tasks')

    def donations(self, obj):
        url = reverse('admin:donations_donation_changelist')
        donations = Donation.objects.filter(order__status__in=['success', 'pending'], order__user=obj).count()
        return format_html('<a href="{}?order__user_id={}">{} {}</a>', url, obj.id, donations, _('donations'))
    donations.short_description = _('Donations')

    def following(self, obj):
        url = reverse('admin:bb_follow_follow_changelist')
        follow_count = Follow.objects.filter(user=obj).count()
        return format_html('<a href="{}?user_id={}">{} objects</a>', url, obj.id, follow_count)
    following.short_description = _('Following')

    def reset_password(self, obj):
        reset_mail_url = reverse('admin:auth_user_password_reset_mail', kwargs={'user_id': obj.id})
        properties.set_tenant(connection.tenant)

        return format_html(
            "<a href='{}'>{}</a>",
            reset_mail_url, _("Send reset password mail")
        )

    def resend_welcome_link(self, obj):
        welcome_mail_url = reverse('admin:auth_user_resend_welcome_mail', kwargs={'user_id': obj.id})
        return format_html(
            "<a href='{}'>{}</a>",
            welcome_mail_url, _("Resend welcome email"),
        )

    def login_as_user(self, obj):
        return format_html(
            u"<a href='/login/user/{}'>{}</a>",
            obj.id,
            _('Login as user')
        )

    def get_inline_instances(self, request, obj=None):
        """ Override get_inline_instances so that the add form does not show inlines """
        if not obj:
            return []
        return super(MemberAdmin, self).get_inline_instances(request, obj)

    def get_urls(self):
        urls = super(MemberAdmin, self).get_urls()

        extra_urls = [
            url(r'^login-as/(?P<user_id>\d+)/$', self.admin_site.admin_view(self.login_as_redirect)),
            url(r'^password-reset/(?P<user_id>\d+)/$',
                self.send_password_reset_mail,
                name='auth_user_password_reset_mail'
                ),
            url(r'^resend_welcome_email/(?P<user_id>\d+)/$',
                self.resend_welcome_email,
                name='auth_user_resend_welcome_mail'
                )
        ]
        return extra_urls + urls

    def send_password_reset_mail(self, request, user_id):
        if not request.user.has_perm('members.change_member'):
            return HttpResponseForbidden('Not allowed to change user')

        user = Member.objects.get(pk=user_id)

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
        return HttpResponseRedirect(reverse('admin:members_member_change', args=(user.id, )))

    def resend_welcome_email(self, request, user_id):
        if not request.user.has_perm('members.change_member'):
            return HttpResponseForbidden('Not allowed to change user')

        user = Member.objects.get(pk=user_id)
        send_welcome_mail(user)
        message = _('User {name} will receive an welcome email.').format(name=user.full_name)
        self.message_user(request, message)

        return HttpResponseRedirect(reverse('admin:members_member_change', args=(user.id, )))

    def login_as_redirect(self, *args, **kwargs):
        user = Member.objects.get(id=kwargs.get('user_id', None))
        token = user.get_login_token()
        url = "/login-with/{}/{}".format(user.pk, token)

        return HttpResponseRedirect(url)

    def login_as_link(self, obj):
        return format_html(
            u"<a target='_blank' href='{}members/member/login-as/{}/'>{}</a>",
            reverse('admin:index'), obj.pk, _('Login as user')
        )
    login_as_link.short_description = _('Login as link')

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Member, MemberAdmin)


class NewGroupChangeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Dynamically set permission widget to make it Tenant aware
        super(NewGroupChangeForm, self).__init__(*args, **kwargs)
        permissions = Permission.objects.all()
        self.fields['permissions'] = PermissionSelectMultipleField(queryset=permissions, required=False)


class GroupsAdmin(GroupAdmin):
    list_display = ["name", ]
    form = NewGroupChangeForm

    class Media:
        css = {
            'all': ('css/admin/permissions-table.css',)
        }

    class Meta:
        model = Group


admin.site.unregister(Group)
admin.site.register(Group, GroupsAdmin)
