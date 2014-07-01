from bluebottle.bb_accounts.models import TimeAvailable
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import get_current_site
from django.conf import settings
from django.template import loader
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from django.utils.http import base36_to_int, int_to_base36

from registration import signals
from registration.models import RegistrationProfile
from rest_framework import status, views, response, generics, viewsets

from bluebottle.bluebottle_drf2.permissions import IsCurrentUserOrReadOnly, IsCurrentUser
from bluebottle.utils.serializers import DefaultSerializerMixin
from rest_framework.permissions import IsAuthenticated

#this belongs now to onepercent should be here in bluebottle

from .serializers import (
    CurrentUserSerializer, UserSettingsSerializer, UserCreateSerializer,
    PasswordResetSerializer, PasswordSetSerializer, BB_USER_MODEL, TimeAvailableSerializer)


class UserProfileDetail(DefaultSerializerMixin, generics.RetrieveUpdateAPIView):
    model = BB_USER_MODEL
    permission_classes = (IsCurrentUserOrReadOnly,)


class UserSettingsDetail(generics.RetrieveUpdateAPIView):
    model = BB_USER_MODEL
    serializer_class = UserSettingsSerializer
    permission_classes = (IsCurrentUser,)


class CurrentUser(generics.RetrieveAPIView):
    model = BB_USER_MODEL
    serializer_class = CurrentUserSerializer

    def get_object(self, queryset=None):
        if isinstance(self.request.user, AnonymousUser):
            raise Http404()
        return self.request.user


class UserCreate(generics.CreateAPIView):
    model = BB_USER_MODEL
    serializer_class = UserCreateSerializer

    def get_name(self):
        return "Users"

    def pre_save(self, obj):
        obj.primary_language = self.request.LANGUAGE_CODE[:2]

    def _login_user(self, request, user):
        # Auto login the user after activation
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        return login(request, user)

    def post_save(self, obj, created=False):
        # Create a RegistrationProfile and email its activation key to the User.
        registration_profile = RegistrationProfile.objects.create_profile(obj)

        # Activate user
        activated_user = RegistrationProfile.objects.activate_user(registration_profile.activation_key)
        if activated_user:
            # Log the user in when the user has been activated and return the current user object.

            self._login_user(self.request, activated_user)
            self.object = activated_user

        # TODO: This should be a welcome email and not an activation email
        #
        if created:
            current_site = get_current_site(self.request)
            site_name = current_site.name
            domain = current_site.domain
            site = 'https://' + domain
            c = {
                'email': obj.email,
                'site': site,
                'site_name': site_name,
                'user': obj,
                'activation_key': registration_profile.activation_key,
                'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                'LANGUAGE_CODE': self.request.LANGUAGE_CODE[:2]
            }
            subject_template_name = 'registration/activation_email_subject.txt'
        
            extension = getattr(settings, 'HTML_ACTIVATION_EMAIL', False) and 'html' or 'txt'
            email_template_name = 'registration/activation_email.' + extension
        
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)
        
            obj.email_user(subject, email)


class UserActivate(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer

    def login_user(self, request, user):
        # Auto login the user after activation
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        return login(request, user)

    def get(self, request, *args, **kwargs):
        activation_key = self.kwargs.get('activation_key', None)
        activated_user = RegistrationProfile.objects.activate_user(activation_key)
        if activated_user:
            # Log the user in when the user has been activated and return the current user object.
            self.login_user(request, activated_user)
            self.object = activated_user
            serializer = self.get_serializer(self.object)
            signals.user_activated.send(sender=self.__class__,
                                        user=activated_user,
                                        request=request)
            return response.Response(serializer.data)
        # Return 400 when the activation didn't work.
        return response.Response(status=status.HTTP_400_BAD_REQUEST)


"""
With a viewsets.ModelViewSet we don't need to create duplicate for
List and Detail, we will use routers for the urls
"""
class TimeAvailableViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides 'list', 'create', 'retrieve',
    'update' and 'destroy actions'.
    """
    queryset = TimeAvailable.objects.all()
    serializer_class = TimeAvailableSerializer
    permission_classes = (IsAuthenticated, )


class PasswordReset(views.APIView):
    """
    Allows a password reset to be initiated for valid users in the system. An email will be sent to the user with a
    password reset link upon successful submission.
    """
    serializer_class = PasswordResetSerializer

    def save(self, password_reset_form, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html', use_https=True,
             token_generator=default_token_generator, from_email=None, request=None):
        """
        Generates a one-use only link for resetting password and sends to the user. This has been ported from the
        Django PasswordResetForm to allow HTML emails instead of plaint text emails.
        """
        # TODO: Create a patch to Django to use user.email_user instead of send_email.
        for user in password_reset_form.users_cache:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            site = 'https://' + domain
            c = {
                'email': user.email,
                'site': site,
                'site_name': site_name,
                'uid': int_to_base36(user.pk),
                'user': user,
                'token': token_generator.make_token(user),
                'LANGUAGE_CODE': self.request.LANGUAGE_CODE[:2]
            }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)
            user.email_user(subject, email)

    def put(self, request, *args, **kwargs):
        password_reset_form = PasswordResetForm()
        serializer = PasswordResetSerializer(password_reset_form=password_reset_form, data=request.DATA)
        if serializer.is_valid():
            opts = {
                # Always use https
                'use_https': True,
                'from_email': settings.DEFAULT_FROM_EMAIL,
                'request': request,
            }
            # TODO: When Django Password Reset form uses user.email_user() this can be enabled and the self.save() can
            #       be removed.
            # password_reset_form.save(**opts)  # Sends the email
            self.save(password_reset_form, **opts)  # Sends the email

            return response.Response(status=status.HTTP_200_OK)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordSet(views.APIView):
    """
    Allows a new password to be set in the resource that is a valid password reset hash.
    """
    serializer_class = PasswordSetSerializer

    def put(self, request, *args, **kwargs):
        # The uidb36 and the token are checked by the URLconf.
        uidb36 = self.kwargs.get('uidb36')
        token = self.kwargs.get('token')
        user_model = get_user_model()
        user = None

        try:
            uid_int = base36_to_int(uidb36)
            user = user_model._default_manager.get(pk=uid_int)
        except (ValueError, OverflowError, user.DoesNotExist):
            pass

        if user is not None and default_token_generator.check_token(user, token):
            password_set_form = SetPasswordForm(user)
            serializer = PasswordSetSerializer(password_set_form=password_set_form, data=request.DATA)
            if serializer.is_valid():
                password_set_form.save()  # Sets the password

                # return a jwt token so the user can be logged in immediately
                return response.Response({'token': user.get_jwt_token()}, status=status.HTTP_200_OK)
            return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return response.Response(status=status.HTTP_404_NOT_FOUND)
