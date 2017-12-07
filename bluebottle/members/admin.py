import six
from adminsortable.admin import SortableTabularInline, NonSortableParentAdmin
from django import forms
from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db import connection
from django.forms.models import ModelFormMetaclass
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_singleton_admin.admin import SingletonAdmin

from bluebottle.bb_accounts.models import UserAddress
from bluebottle.members.models import CustomMemberFieldSettings, CustomMemberField, MemberPlatformSettings
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.votes.models import Vote
from bluebottle.clients import properties

from .models import Member

BB_USER_MODEL = get_user_model()


class MemberCreationForm(forms.ModelForm):
    """
    A form that creates a member, with no privileges, from the given email.
    """
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
    }
    email = forms.EmailField(label=_("email address"), max_length=254,
                             help_text=_(
                                 "Required. 254 characters or fewer. A valid email address."))
    first_name = forms.CharField(label=_("first name"), max_length=100)
    last_name = forms.CharField(label=_("last name"), max_length=100,)

    class Meta:
        model = BB_USER_MODEL
        fields = ("email",)

    def clean_email(self):
        # Since BlueBottleUser.email is unique, this check is redundant but it sets a nicer error message than the ORM.
        email = self.cleaned_data["email"]
        try:
            BB_USER_MODEL._default_manager.get(email=email)
        except BB_USER_MODEL.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def save(self, commit=True):
        user = super(MemberCreationForm, self).save(commit=False)
        user.is_active = True
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
                             help_text=_(
                                 "Required. 254 characters or fewer. A valid email address."))
    password = ReadOnlyPasswordHashField(label=_("Password"),
                                         help_text=_(
                                             "Raw passwords are not stored, so there is no way to see "
                                             "this user's password, but you can change the password "
                                             "using <a href=\"../password/\">this form</a>."))

    class Meta:
        model = BB_USER_MODEL
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


class MemberVotesInline(admin.TabularInline):
    model = Vote
    readonly_fields = ('project', 'created')
    fields = ('project', 'created',)
    extra = 0


class MemberAdmin(UserAdmin):

    @property
    def standard_fieldsets(self):

        standard_fieldsets = [
            [None, {'fields': ['email', 'password', 'remote_id']}],
            [_('Personal info'),
             {'fields': ['first_name', 'last_name', 'username', 'gender', 'birthdate', 'phone_number']}],
            [_("Profile"),
             {'fields': ['user_type', 'is_co_financer', 'picture', 'about_me', 'location', 'partner_organization']}],
            [_("Settings"),
             {'fields': ['primary_language', 'newsletter', 'campaign_notifications']}],
            [_('Skills & interests'),
             {'fields': ['favourite_themes', 'skills']}],
            [_('Important dates'),
             {'fields': ['last_login', 'date_joined', 'deleted']}],
        ]

        for item in properties.PAYMENT_METHODS:
            if item['name'] == 'Pledge':
                standard_fieldsets[2][1]['fields'].append('can_pledge')

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
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields': ('email', 'first_name', 'last_name',)}
         ),
    )

    readonly_fields = ('date_joined', 'last_login', 'updated', 'deleted', 'login_as_user')

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

    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser', 'newsletter', 'favourite_themes', 'skills')
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'is_active', 'login_as_user')
    ordering = ('-date_joined', 'email',)
    inlines = (UserAddressInline, MemberVotesInline,)

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
            url(r'^login-as/(?P<user_id>\d+)/$', self.admin_site.admin_view(self.login_as_redirect))
        ]
        return extra_urls + urls

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
