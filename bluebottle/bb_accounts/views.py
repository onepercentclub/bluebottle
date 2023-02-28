import json
from datetime import timedelta
import uuid
import requests
from collections import namedtuple

from axes.utils import reset
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.http import Http404
from django.template import loader
from django.utils import timezone
from django.utils.http import base36_to_int, int_to_base36
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import status, response, generics, parsers
from rest_framework.exceptions import PermissionDenied, NotAuthenticated, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.views import ObtainJSONWebTokenView
from tenant_extras.utils import TenantLanguage

from bluebottle.bb_accounts.permissions import (
    CurrentUserPermission, IsAuthenticatedOrOpenPermission
)
from bluebottle.bb_accounts.utils import send_welcome_mail
from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url
from bluebottle.initiatives.serializers import MemberSerializer, CurrentMemberSerializer
from bluebottle.members.messages import SignUptokenMessage
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.members.models import UserActivity
from bluebottle.members.serializers import (
    UserCreateSerializer, ManageProfileSerializer, UserProfileSerializer,
    PasswordResetSerializer, CurrentUserSerializer,
    UserVerificationSerializer, UserDataExportSerializer, TokenLoginSerializer,
    EmailSetSerializer, PasswordUpdateSerializer, SignUpTokenSerializer,
    SignUpTokenConfirmationSerializer, UserActivitySerializer,
    CaptchaSerializer, AxesJSONWebTokenSerializer, MemberSignUpSerializer,
    PasswordStrengthSerializer, PasswordResetConfirmSerializer, AuthTokenSerializer,
    OldUserActivitySerializer, MemberProfileSerializer
)
from bluebottle.members.tokens import login_token_generator
from bluebottle.utils.email_backend import send_mail
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.permissions import IsCurrentUser
from bluebottle.utils.views import (
    RetrieveAPIView, UpdateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin, CreateAPIView
)

USER_MODEL = get_user_model()


class AxesObtainJSONWebToken(ObtainJSONWebTokenView):
    """
    API View that receives a POST with a user's username and password.

    Returns a JSON Web Token that can be used for authenticated requests.
    """
    serializer_class = AxesJSONWebTokenSerializer
    parser_classes = (parsers.JSONParser, )


class AuthView(JsonApiViewMixin, CreateAPIView):

    def perform_create(self, serializer):
        model = namedtuple('Model', ('pk', 'email', 'password', 'token'))

        serializer.instance = model(
            str(uuid.uuid4()),
            serializer.validated_data['user'].email,
            '**************',
            serializer.validated_data['token']
        )
        return serializer.validated_data

    serializer_class = AuthTokenSerializer


class CaptchaVerification(JsonApiViewMixin, CreateAPIView):
    serializer_class = CaptchaSerializer

    def perform_create(self, serializer):
        ip = get_client_ip(self.request)
        reset(ip=ip)

        model = namedtuple('Model', ('pk', 'token'))

        serializer.instance = model(
            str(uuid.uuid4()),
            serializer.validated_data['token']
        )
        return serializer.validated_data


class UserProfileDetail(RetrieveAPIView):
    """
    Fetch User Details

    """
    queryset = USER_MODEL.objects.all()
    serializer_class = UserProfileSerializer

    permission_classes = [IsAuthenticatedOrOpenPermission]


class OldUserActivityDetail(CreateAPIView):
    """

    """
    queryset = UserActivity.objects.all()
    serializer_class = OldUserActivitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)


class UserActivityDetail(JsonApiViewMixin, CreateAPIView):
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
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


class CurrentMemberDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveAPIView):
    """
    Retrieve details about the member
    """
    queryset = USER_MODEL.objects.all()
    serializer_class = CurrentMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, *args, **kwargs):
        return self.request.user


class MemberProfileDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    """
    Retrieve details about the member
    """
    queryset = USER_MODEL.objects.all()
    serializer_class = MemberProfileSerializer
    permission_classes = [IsCurrentUser]


class MemberDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveAPIView):
    """
    Retrieve details about the member
    """
    queryset = USER_MODEL.objects.all()
    serializer_class = MemberSerializer

    permission_classes = [IsAuthenticatedOrOpenPermission]


class MemberSignUp(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    """
    Retrieve details about the member
    """
    queryset = USER_MODEL.objects.all()
    serializer_class = MemberSignUpSerializer

    permission_classes = []

    def perform_create(self, serializer):
        return serializer.save(is_active=True)


class PasswordStrengthDetail(JsonApiViewMixin, generics.CreateAPIView):
    serializer_class = PasswordStrengthSerializer

    def perform_create(self, serializer, *args, **kwargs):
        serializer.is_valid(raise_exception=True)

        model = namedtuple('Model', 'pk')
        serializer.instance = model(str(uuid.uuid4()))


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
    parser_classes = (parsers.JSONParser, )

    def create(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            self.request.user.last_logout = timezone.now()
            self.request.user.save()

        return response.Response('', status=status.HTTP_204_NO_CONTENT)


class SignUpToken(JsonApiViewMixin, CreateAPIView):
    """
    Request a signup token

    """
    permission_classes = []

    queryset = USER_MODEL.objects.all()
    serializer_class = SignUpTokenSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        token = TimestampSigner().sign(instance.pk)
        SignUptokenMessage(
            instance,
            custom_message={
                'token': token,
                'url': serializer.validated_data.get('url', ''),
                'segment_id': serializer.validated_data.get('segment_id', '')
            },
        ).compose_and_send()
        return instance


class SignUpTokenConfirmation(JsonApiViewMixin, CreateAPIView):
    """
    Confirm a signup token

    """
    queryset = USER_MODEL.objects.all()
    serializer_class = SignUpTokenConfirmationSerializer
    permission_classes = []

    def perform_create(self, serializer):

        try:
            signer = TimestampSigner()
            member = self.queryset.get(
                pk=signer.unsign(serializer.validated_data['token'], max_age=timedelta(hours=24))
            )

            if member.is_active:
                raise ValidationError({'token': _('The link to activate your account has already been used.')})

        except SignatureExpired:
            raise ValidationError({'token': _('The link to activate your account has expired. Please sign up again.')})
        except BadSignature:
            raise ValidationError({'token': _('Something went wrong on our side. Please sign up again.')})

        serializer.instance = member
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


class PasswordResetConfirm(JsonApiViewMixin, CreateAPIView):
    """
    Allows a new password to be set in the resource that is a valid password
    reset hash.
    """

    serializer_class = PasswordResetConfirmSerializer

    def perform_create(self, serializer):
        # The uidb36 and the token are checked by the URLconf.
        try:
            uidb36, token = serializer.validated_data['token'].split('-', 1)
        except ValueError:
            raise ValidationError('Invalid token')

        user = USER_MODEL.objects.get(pk=base36_to_int(uidb36))

        if default_token_generator.check_token(user, token):

            user.set_password(serializer.validated_data['password'])
            user.save()

            # return a jwt token so the user can be logged in immediately
            serializer.validated_data['jwt_token'] = user.get_jwt_token()

            model = namedtuple('Model', ('pk', 'password', 'jwt_token', 'token'))
            serializer.instance = model(
                str(uuid.uuid4()),
                '*******',
                serializer.validated_data['jwt_token'],
                serializer.validated_data['token'],
            )
        else:
            raise ValidationError('Token expired')

    def get(self, *args, **kwargs):
        user = self._get_user(self.kwargs.get('uidb36'))
        token = self.kwargs.get('token')

        if user is not None and default_token_generator.check_token(user,
                                                                    token):
            return response.Response(status=status.HTTP_200_OK)
        return response.Response({'message': 'Token expired'},
                                 status=status.HTTP_400_BAD_REQUEST)


class PasswordReset(JsonApiViewMixin, CreateAPIView):
    """
    Allows a password reset to be initiated for valid users in the system. An
    email will be sent to the user with a
    password reset link upon successful submission.
    """
    serializer_class = PasswordResetSerializer

    def perform_create(self, serializer):
        try:
            user = USER_MODEL.objects.get(email__iexact=serializer.validated_data['email'], is_active=True)
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

        model = namedtuple('Model', ('pk', 'email'))
        serializer.instance = model(str(uuid.uuid4()), serializer.validated_data['email'])


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
