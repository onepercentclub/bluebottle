import six
from adminfilters.multiselect import UnionFieldListFilter
from adminsortable.admin import SortableTabularInline, NonSortableParentAdmin
from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.urlresolvers import reverse
from django.db import connection
from django.forms.models import ModelFormMetaclass
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from django_singleton_admin.admin import SingletonAdmin

from bluebottle.bb_accounts.models import UserAddress
from bluebottle.donations.models import Donation
from bluebottle.geo.models import Location
from bluebottle.members.models import CustomMemberFieldSettings, CustomMemberField, MemberPlatformSettings
from bluebottle.projects.models import Project
from bluebottle.tasks.models import Task
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.clients import properties

from .models import Member


class MemberCreationForm(forms.ModelForm):
    """
    A form that creates a member, with no privileges, from the given email.
    """
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
    }
    email = forms.EmailField(label=_("Email address"), max_length=254,
                             help_text=_("A valid, unique email address."))

    is_active = forms.BooleanField(label=_("Is active"), initial=True)

    class Meta:
        model = Member
        fields = ('email', 'first_name', 'last_name',
                  'is_active', 'is_staff', 'is_superuser')

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


class MemberPlatformSettingsAdmin(SingletonAdmin, NonSortableParentAdmin):

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


class MemberChangeForm(six.with_metaclass(CustomAdminFormMetaClass, forms.ModelForm)):
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

    @property
    def standard_fieldsets(self):

        standard_fieldsets = [
            [_("Main"), {'fields': [
                'remote_id',
                'email',
                'first_name',
                'last_name',
                'username',
                'phone_number',
                'reset_password',
                'last_login',
                'date_joined',
                'deleted',
                'is_co_financer',
                'partner_organization',
                'campaign_notifications',
                'newsletter',
                'primary_language',
            ]}],
            [_("Profile"),
             {'fields': [
                 'picture',
                 'about_me',
                 'favourite_themes',
                 'skills'
             ]}],
            [_('Engagement'),
             {'fields': [
                 'projects_managed',
                 'tasks',
                 'donations'
             ]}],
        ]

        if Location.objects.count():
            standard_fieldsets[1][1]['fields'].append('location')

        for item in properties.PAYMENT_METHODS:
            if item['name'] == 'Pledge':
                standard_fieldsets[0][1]['fields'].append('can_pledge')

        if CustomMemberFieldSettings.objects.count():
            extra = (_('Extra fields'), {
                'fields': [field.slug for field in CustomMemberFieldSettings.objects.all()]
            })

            standard_fieldsets.append(extra)

        return tuple(standard_fieldsets)

    staff_fieldsets = (
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'groups')}),
    )

    superuser_fieldsets = (
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
    )

    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields': ('email', 'first_name', 'last_name',
                           'is_active', 'is_staff', 'is_superuser')}
         ),
    )

    readonly_fields = ('date_joined', 'last_login',
                       'updated', 'deleted', 'login_as_user',
                       'reset_password', 'projects_managed',
                       'tasks', 'donations')

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
        'user_type',
        'is_active',
        'is_staff',
        'is_superuser',
        'newsletter',
        ('favourite_themes', UnionFieldListFilter),
        ('skills', UnionFieldListFilter),
        'groups'
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

    def donations(self, obj):
        url = reverse('admin:donations_donation_changelist')
        donations = Donation.objects.filter(order__status__in=['success', 'pending'], order__user=obj).count()
        return format_html('<a href="{}?order__user_id={}">{} {}</a>', url, obj.id, donations, _('donations'))

    def reset_password(self, obj):
        reset_form_url = reverse('admin:auth_user_password_change', args=(obj.id, ))
        reset_mail_url = reverse('admin:auth_user_password_reset_mail', kwargs={'user_id': obj.id})
        return format_html("<a href='{}'>{}</a>  | <a href='{}'>{}</a>  ",
                           reset_form_url, _("Reset password form"),
                           reset_mail_url, _("Send reset password mail"))

    def login_as_user(self, obj):
        return format_html(
            u"<a href='/login/user/{}'>{}</a>",
            obj.id,
            'Login as user'
        )

    def change_view(self, request, *args, **kwargs):
        # for superuser
        try:
            if request.user.is_superuser:
                self.fieldsets = self.standard_fieldsets + self.superuser_fieldsets
            else:
                self.fieldsets = self.standard_fieldsets + self.staff_fieldsets

            response = UserAdmin.change_view(self, request, *args, **kwargs)
        finally:
            # Reset fieldsets to its original value
            self.fieldsets = self.standard_fieldsets

        return response

    def __init__(self, *args, **kwargs):
        super(MemberAdmin, self).__init__(*args, **kwargs)

        self.list_display = (
            'email', 'first_name', 'last_name', 'is_staff', 'date_joined',
            'is_active', 'login_as_link')

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
                )
        ]
        return extra_urls + urls

    def send_password_reset_mail(self, request, user_id):
        user = Member.objects.get(pk=user_id)
        form = PasswordResetForm({'email': user.email})
        form.is_valid()
        opts = {
            'use_https': True,
            'token_generator': default_token_generator,
            'from_email': properties.TENANT_MAIL_PROPERTIES['address'],
            'request': request,
        }
        form.save(**opts)
        message = _('User {name} will receive an email to reset password.').format(name=user.full_name)
        self.message_user(request, message)
        return HttpResponseRedirect(reverse('admin:members_member_change', args=(user.id, )))

    def login_as_redirect(self, *args, **kwargs):
        user = Member.objects.get(id=kwargs.get('user_id', None))
        url = "/login-with/{0}".format(user.get_jwt_token())

        return HttpResponseRedirect(url)

    def login_as_link(self, obj):
        return format_html(
            u"<a target='_blank' href='{}members/member/login-as/{}/'>{}</a>",
            reverse('admin:index'), obj.pk, 'Login as user'
        )


admin.site.register(Member, MemberAdmin)


class GroupsAdmin(admin.ModelAdmin):
    list_display = ["name", ]

    class Media:
        css = {
            'all': ('css/admin/permissions-table.css',)
        }

    class Meta:
        model = Group


admin.site.unregister(Group)
admin.site.register(Group, GroupsAdmin)
