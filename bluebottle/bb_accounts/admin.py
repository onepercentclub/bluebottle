from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


BB_USER_MODEL = get_user_model()


class BlueBottleUserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given email and password.
    """
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    email = forms.EmailField(label=_("email address"), max_length=254,
                             help_text=_("Required. 254 characters or fewer. A valid email address."))
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above, for verification."))

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

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        user = super(BlueBottleUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class BlueBottleUserChangeForm(forms.ModelForm):
    email = forms.EmailField(label=_("email address"), max_length=254,
                             help_text=_("Required. 254 characters or fewer. A valid email address."))
    password = ReadOnlyPasswordHashField(label=_("Password"),
                                         help_text=_("Raw passwords are not stored, so there is no way to see "
                                                     "this user's password, but you can change the password "
                                                     "using <a href=\"password/\">this form</a>."))

    class Meta:
        model = BB_USER_MODEL

    def __init__(self, *args, **kwargs):
        super(BlueBottleUserChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class BlueBottleUserAdmin(UserAdmin):
    # TODO: this should be easier to override
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'username', 'gender', 'birthdate', 'phone_number')}),
        (_("Profile"), {'fields': ('user_type', 'picture', 'about', 'why', 'time_available', 'location', 'website', 'tags')}),
        (_("Settings"), {'fields': ['primary_language', 'newsletter']}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'deleted')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )

    readonly_fields = ('date_joined', 'last_login', 'updated', 'deleted', 'login_as_user')

    form = BlueBottleUserChangeForm
    add_form = BlueBottleUserCreationForm

    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser')

    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'is_active', 'login_as_user')
    ordering = ('-date_joined', 'email',)

    def login_as_user(self, obj):
        return "<a href='/login/user/{0}'>{1}</a>".format(obj.id, 'Login as user')

    login_as_user.allow_tags = True

if settings.AUTH_USER_MODEL == 'accounts.BlueBottleUser':
   admin.site.register(BB_USER_MODEL, BlueBottleUserAdmin)
