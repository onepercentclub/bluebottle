from datetime import timedelta
from django.utils.timezone import now
import json
import requests

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.template import loader
from django.http import Http404
from django.utils.http import base36_to_int, int_to_base36
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from rest_framework import status, views, response, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotAuthenticated, ValidationError

from rest_framework_jwt.views import ObtainJSONWebToken

from rest_framework_json_api.views import AutoPrefetchMixin

from axes.utils import reset

from bluebottle.bb_accounts.permissions import (
    CurrentUserPermission, IsAuthenticatedOrOpenPermission
)
from bluebottle.bb_accounts.utils import send_welcome_mail
from bluebottle.members.models import UserActivity
from bluebottle.utils.views import RetrieveAPIView, UpdateAPIView, JsonApiViewMixin, CreateAPIView

from tenant_extras.utils import TenantLanguage

from bluebottle.utils.email_backend import send_mail
from bluebottle.clients.utils import tenant_url
from bluebottle.clients import properties
from bluebottle.initiatives.serializers import MemberSerializer
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.members.serializers import (
    UserCreateSerializer, ManageProfileSerializer, UserProfileSerializer,
    PasswordResetSerializer, PasswordSetSerializer, CurrentUserSerializer,
    UserVerificationSerializer, UserDataExportSerializer, TokenLoginSerializer,
    EmailSetSerializer, PasswordUpdateSerializer, SignUpTokenSerializer,
    SignUpTokenConfirmationSerializer, UserActivitySerializer,
    CaptchaSerializer, AxesJSONWebTokenSerializer
)
from bluebottle.members.tokens import login_token_generator
from bluebottle.utils.utils import get_client_ip

USER_MODEL = get_user_model()


class AxesObtainJSONWebToken(ObtainJSONWebToken):
    """
    API View that receives a POST with a user's username and password.

    Returns a JSON Web Token that can be used for authenticated requests.
    """
    serializer_class = AxesJSONWebTokenSerializer


class CaptchaVerification(generics.CreateAPIView):
    serializer_class = CaptchaSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)

        ip = get_client_ip(request)
        reset(ip=ip)

        return response.Response(status=status.HTTP_201_CREATED)


class UserProfileDetail(RetrieveAPIView):
    """
    Fetch User Details

    """
    queryset = USER_MODEL.objects.all()
    serializer_class = UserProfileSerializer

    permission_classes = [IsAuthenticatedOrOpenPermission]


class UserActivityDetail(CreateAPIView):
    """

    """
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated():
            serializer.save(user=self.request.user)


class ManageProfileDetail(generics.RetrieveUpdateDestroyAPIView):
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
    queryset = USER_MODEL.objects.all()
    permission_classes = (CurrentUserPermission, )
    serializer_class = ManageProfileSerializer

    def get_serializer(self, *args, **kwargs):
        kwargs['partial'] = True
        return super(ManageProfileDetail, self).get_serializer(
            *args, **kwargs
        )

    def perform_update(self, serializer):
        try:
            # Read only properties come from the TOKEN_AUTH / SAML settings
            assertion_mapping = properties.TOKEN_AUTH['assertion_mapping']
            user_properties = list(assertion_mapping.keys())

            # Ensure read-only user properties are not being changed
            for prop in [prop for prop in user_properties if prop in serializer.validated_data]:
                if getattr(serializer.instance, prop) != serializer.validated_data.get(prop):
                    raise PermissionDenied

        except (AttributeError, KeyError):
            pass

        super(ManageProfileDetail, self).perform_update(serializer)

    def perform_destroy(self, instance):
        instance.anonymize()


class MemberDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveAPIView):
    """
    Retrieve details about the member
    """
    queryset = USER_MODEL.objects.all()
    serializer_class = MemberSerializer

    permission_classes = (CurrentUserPermission, )

    def get_object(self):
        if isinstance(self.request.user, AnonymousUser):
            raise Http404()
        return self.request.user


class CurrentUser(RetrieveAPIView):
    """
    Fetch Current User

    """
    queryset = USER_MODEL.objects.all()
    serializer_class = CurrentUserSerializer

    permission_classes = (CurrentUserPermission, )

    def get_object(self):
        if isinstance(self.request.user, AnonymousUser):
            raise Http404()
        return self.request.user


class Logout(generics.CreateAPIView):
    """
    Log the user out

    """
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            self.request.user.last_logout = timezone.now()
            self.request.user.save()

        return response.Response('', status=status.HTTP_204_NO_CONTENT)


class SignUpToken(generics.CreateAPIView):
    """
    Request a signup token

    """
    queryset = USER_MODEL.objects.all()
    serializer_class = SignUpTokenSerializer


class SignUpTokenConfirmation(generics.UpdateAPIView):
    """
    Confirm a signup token

    """
    queryset = USER_MODEL.objects.all()
    serializer_class = SignUpTokenConfirmationSerializer

    def get_object(self):
        try:
            signer = TimestampSigner()
            member = self.queryset.get(
                pk=signer.unsign(self.kwargs['pk'], max_age=timedelta(hours=2))
            )

            if member.is_active:
                raise ValidationError({'id': _('The link to activate your account has already been used.')})

            return member
        except SignatureExpired:
            raise ValidationError({'id': _('The link to activate your account has expired. Please sign up again.')})
        except BadSignature:
            raise ValidationError({'id': _('Something went wrong on our side. Please sign up again.')})

    def perform_update(self, serializer):
        serializer.save(is_active=True)
        send_welcome_mail(serializer.instance)


class UserCreate(generics.CreateAPIView):
    """
    Create User

    """
    queryset = USER_MODEL.objects.all()
    serializer_class = UserCreateSerializer

    def get_name(self):
        return "Users"

    def perform_create(self, serializer):
        settings = MemberPlatformSettings.objects.get()
        if settings.closed:
            raise PermissionDenied()
        if 'primary_language' not in serializer.validated_data:
            serializer.save(primary_language=properties.LANGUAGE_CODE, is_active=True)
        else:
            serializer.save(is_active=True)


class PasswordReset(views.APIView):
    """
    Allows a password reset to be initiated for valid users in the system. An
    email will be sent to the user with a
    password reset link upon successful submission.
    """
    def put(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = USER_MODEL.objects.get(email__iexact=serializer.validated_data['email'])
            context = {
                'email': user.email,
                'site': tenant_url(),
                'site_name': tenant_url(),
                'uid': int_to_base36(user.pk),
                'user': user,
                'token': default_token_generator.make_token(user),
            }

            with TenantLanguage(user.primary_language):
                subject = loader.render_to_string('bb_accounts/password_reset_subject.txt', context)
                # Email subject *must not* contain newlines
                subject = ''.join(subject.splitlines())

            send_mail(
                template_name='bb_accounts/password_reset_email',
                to=user,
                subject=subject,
                **context
            )
        except USER_MODEL.DoesNotExist:
            pass

        return response.Response({}, status=status.HTTP_200_OK)


class PasswordProtectedMemberUpdateApiView(UpdateAPIView):
    queryset = USER_MODEL.objects.all()

    permission_classes = (CurrentUserPermission, )

    def get_object(self):
        if isinstance(self.request.user, AnonymousUser):
            raise NotAuthenticated()
        return self.request.user

    def perform_update(self, serializer):
        password = serializer.validated_data.pop('password')

        if not self.request.user.check_password(password):
            raise PermissionDenied('Platform is closed')

        self.request.user.last_logout = now()
        self.request.user.save()

        return super(PasswordProtectedMemberUpdateApiView, self).perform_update(serializer)


class EmailSetView(PasswordProtectedMemberUpdateApiView):
    serializer_class = EmailSetSerializer


class PasswordSetView(PasswordProtectedMemberUpdateApiView):
    serializer_class = PasswordUpdateSerializer


class PasswordSet(views.APIView):
    """
    Allows a new password to be set in the resource that is a valid password
    reset hash.
    """
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

        if user is not None and default_token_generator.check_token(
                user, token):

            serializer = PasswordSetSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user.set_password(serializer.validated_data['new_password1'])
            user.save()

            # return a jwt token so the user can be logged in immediately
            return response.Response({'token': user.get_jwt_token()},
                                     status=status.HTTP_200_OK)

        return response.Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, *args, **kwargs):
        user = self._get_user(self.kwargs.get('uidb36'))
        token = self.kwargs.get('token')

        if user is not None and default_token_generator.check_token(user,
                                                                    token):
            return response.Response(status=status.HTTP_200_OK)
        return response.Response({'message': 'Token expired'},
                                 status=status.HTTP_400_BAD_REQUEST)


class TokenLogin(generics.CreateAPIView):

    serializer_class = TokenLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data['user_id']
        token = serializer.validated_data['token']

        try:
            user = USER_MODEL.objects.get(pk=user_id)
        except USER_MODEL.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

        if login_token_generator.check_token(user, token):
            user.last_login = now()
            user.save()

            return response.Response(
                {'token': user.get_jwt_token()},
                status=status.HTTP_201_CREATED
            )

        return response.Response(status=status.HTTP_404_NOT_FOUND)


class UserVerification(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = USER_MODEL.objects.all()
    serializer_class = UserVerificationSerializer

    def perform_create(self, serializer):
        verification_response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': properties.RECAPTCHA_SECRET,
                'response': serializer.validated_data['token']
            }
        )
        data = json.loads(verification_response.content)

        if data.get('success'):
            self.request.user.verified = True
            self.request.user.save()
        else:
            raise PermissionDenied('Could not verify token')


class UserDataExport(generics.RetrieveAPIView):
    queryset = USER_MODEL.objects.all()
    serializer_class = UserDataExportSerializer

    permission_classes = (CurrentUserPermission, )

    def get_object(self):
        if isinstance(self.request.user, AnonymousUser):
            raise Http404()

        return self.request.user
