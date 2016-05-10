from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.utils import translation
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.template import loader
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from django.utils.http import base36_to_int, int_to_base36
from django.utils.translation import ugettext_lazy as _
from importlib import import_module

from rest_framework import status, views, response, generics
from tenant_extras.drf_permissions import TenantConditionalOpenClose

from bluebottle.utils.email_backend import send_mail
from bluebottle.bluebottle_drf2.permissions import IsCurrentUser
from bluebottle.clients.utils import tenant_url, tenant_name
from bluebottle.clients import properties
from bluebottle.members.serializers import (
    UserCreateSerializer, ManageProfileSerializer, UserProfileSerializer,
    PasswordResetSerializer, PasswordSetSerializer)

USER_MODEL = get_user_model()


class UserProfileDetail(generics.RetrieveAPIView):
    """
    Fetch User Details

    """
    model = USER_MODEL
    permission_classes = (TenantConditionalOpenClose,)
    serializer_class = UserProfileSerializer


class ManageProfileDetail(generics.RetrieveUpdateAPIView):
    """
    Manage User Details
    ---
    PUT:
        serializer: ManageProfileSerializer
        omit_serializer: false
        parameters_strategy: merge
        parameters:
            - name: location
              type: geo.Location
              paramType: form
            - name: avatar
              type: file
        responseMessages:
            - code: 401
              message: Not authenticated
        consumes:
            - application/json
            - multipart/form-data
        produces:
            - application/json
    """
    documentable = True
    model = USER_MODEL
    permission_classes = (TenantConditionalOpenClose, IsCurrentUser)
    serializer_class = ManageProfileSerializer

    def pre_save(self, obj):
        if obj.location:
            # When the location changes, make sure we set the user's country.
            # This decides the payment method they use for example
            obj.address.country = obj.location.country

        try:
            # Read only properties come from the TOKEN_AUTH / SAML settings
            assertion_mapping = properties.TOKEN_AUTH['assertion_mapping']
            user_properties = assertion_mapping.keys()

            # Ensure read-only user properties are not being changed
            previous = USER_MODEL.objects.get(pk=obj.pk)
            for prop in user_properties:
                if getattr(previous, prop) != getattr(obj, prop):
                    raise PermissionDenied

        except (AttributeError, KeyError):
            # Continue if the tenant doesn't have read-only fields
            super(ManageProfileDetail, self).pre_save(obj)


class CurrentUser(generics.RetrieveAPIView):
    """
    Fetch Current User

    """
    model = USER_MODEL

    def get_serializer_class(self):
        dotted_path = self.model._meta.current_user_serializer
        bits = dotted_path.split('.')
        module_name = '.'.join(bits[:-1])
        module = import_module(module_name)
        cls_name = bits[-1]
        return getattr(module, cls_name)

    def get_object(self, queryset=None):
        if isinstance(self.request.user, AnonymousUser):
            raise Http404()
        return self.request.user


class UserCreate(generics.CreateAPIView):
    """
    Create User

    """
    model = USER_MODEL
    serializer_class = UserCreateSerializer

    def get_name(self):
        return "Users"

    def pre_save(self, obj):
        if not obj.primary_language:
            obj.primary_language = properties.LANGUAGE_CODE

    # Overriding the default create so that we can return extra info in the
    # response
    # if there is already a user with the same email address
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return response.Response(serializer.data,
                                     status=status.HTTP_201_CREATED,
                                     headers=headers)

        # If the error is due to a conflict with an existing user then the API
        # reponse should include these details
        errors = serializer.errors
        try:
            if 'email' in request.DATA:
                user = USER_MODEL.objects.get(email=request.DATA['email'])

                # Return whether the conflict was with a user created via
                # email or social auth
                conflict = {
                    'email': user.email,
                    'id': user.id
                }

                # We assume if they have a social auth associated then they use
                # it
                if user.social_auth.count() > 0:
                    social_auth = user.social_auth.all()[0]
                    conflict['provider'] = social_auth.provider
                    conflict['type'] = 'social'
                else:
                    conflict['type'] = 'email'

                if errors.get('non_field_errors', None):
                  errors['non_field_errors'].append(conflict)
                else:
                  errors['non_field_errors'] = [conflict]

        except USER_MODEL.DoesNotExist:
            pass

        # TODO: should we be returing something like a 409_CONFLICT if there is
        # already
        # an existing user with the same emails address?
        return response.Response(errors, status=status.HTTP_400_BAD_REQUEST)

    def post_save(self, obj, created=False):
        if created:
            # Manually set the is_active flag on a user now that we stopped
            # using the Registration manager
            obj.is_active = True
            obj.save()
            # Sending a welcome mail is now done via a post_save signal on a
            # user model


class PasswordResetForm(forms.Form):
    error_messages = {
        'unknown': _("That email address doesn't have an associated "
                     "user account. Are you sure you've registered?"),
        'unusable': _("The user account associated with this email "
                      "address cannot reset the password."),
    }
    email = forms.EmailField(label=_("Email"), max_length=254)

    def clean_email(self):
        """
        Validates that an active user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        self.users_cache = USER_MODEL._default_manager.filter(
            email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        if not any(user.is_active for user in self.users_cache):
            # none of the filtered users are active
            raise forms.ValidationError(self.error_messages['unknown'])
        if any((user.password == UNUSABLE_PASSWORD_PREFIX)
               for user in self.users_cache):
            raise forms.ValidationError(self.error_messages['unusable'])
        return email


class PasswordReset(views.APIView):
    """
    Allows a password reset to be initiated for valid users in the system. An
    email will be sent to the user with a
    password reset link upon successful submission.
    """
    serializer_class = PasswordResetSerializer

    def save(self, password_reset_form, domain_override=None,
             subject_template_name='bb_accounts/password_reset_subject.txt',
             email_template_name='bb_accounts/password_reset_email',
             use_https=True,
             token_generator=default_token_generator, from_email=None,
             request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user. This has been ported from the
        Django PasswordResetForm to allow HTML emails instead of plaint text
        emails.
        """
        # TODO: Create a patch to Django to use user.email_user instead of
        # send_email.
        email = password_reset_form.cleaned_data["email"]

        active_users = USER_MODEL._default_manager.filter(
            email__iexact=email, is_active=True)
        for user in active_users:
            if not domain_override:
                site_name = tenant_name()
                domain = tenant_url()
            else:
                site_name = domain = domain_override

            c = {
                'email': user.email,
                'site': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.pk),
                'user': user,
                'token': token_generator.make_token(user),
                'LANGUAGE_CODE': self.request.LANGUAGE_CODE[:2]
            }

            cur_language = translation.get_language()

            if user.primary_language:
                translation.activate(user.primary_language)
            else:
                translation.activate(properties.LANGUAGE_CODE)

            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())

            translation.activate(cur_language)

            send_mail(
                template_name=email_template_name,
                to=user,
                subject=subject,
                **c
            )

    def put(self, request, *args, **kwargs):
        password_reset_form = PasswordResetForm()
        serializer = PasswordResetSerializer(
            password_reset_form=password_reset_form, data=request.DATA)
        if serializer.is_valid():
            opts = {
                # Always use https
                'use_https': True,
                'from_email': settings.DEFAULT_FROM_EMAIL,
                'request': request,
            }
            # TODO: When Django Password Reset form uses user.email_user()
            # this can be enabled and the self.save() can
            #       be removed.
            # password_reset_form.save(**opts)  # Sends the email
            self.save(password_reset_form, **opts)  # Sends the email

            return response.Response(status=status.HTTP_200_OK)
        return response.Response(serializer.errors,
                                 status=status.HTTP_400_BAD_REQUEST)


class PasswordSet(views.APIView):
    """
    Allows a new password to be set in the resource that is a valid password
    reset hash.
    """
    serializer_class = PasswordSetSerializer

    def _get_user(self, uidb36):
        try:
            uid_int = base36_to_int(uidb36)
            user = USER_MODEL._default_manager.get(pk=uid_int)
        except (ValueError, OverflowError, USER_MODEL.DoesNotExist):
            user = None

        return user

    def put(self, request, *args, **kwargs):
        # The uidb36 and the token are checked by the URLconf.

        user = self._get_user(self.kwargs.get('uidb36'))
        token = self.kwargs.get('token')

        if user is not None and default_token_generator.check_token(user,
                                                                    token):
            password_set_form = SetPasswordForm(user)
            serializer = PasswordSetSerializer(
                password_set_form=password_set_form, data=request.DATA)
            if serializer.is_valid():
                password_set_form.save()  # Sets the password

                # return a jwt token so the user can be logged in immediately
                return response.Response({'token': user.get_jwt_token()},
                                         status=status.HTTP_200_OK)
            return response.Response(serializer.errors,
                                     status=status.HTTP_400_BAD_REQUEST)

        return response.Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, *args, **kwargs):
        user = self._get_user(self.kwargs.get('uidb36'))
        token = self.kwargs.get('token')

        if user is not None and default_token_generator.check_token(user,
                                                                    token):
            return response.Response(status=status.HTTP_200_OK)
        return response.Response({'message': 'Token expired'},
                                  status=status.HTTP_400_BAD_REQUEST)


class DisableAccount(views.APIView):

    def post(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        token = self.kwargs.get("token")

        user = USER_MODEL.objects.get(id=int(user_id))

        if user.get_disable_token() != token:
            return response.Response(status=status.HTTP_400_BAD_REQUEST)

        user.is_active = False
        user.save()
        return response.Response(status=status.HTTP_200_OK)
