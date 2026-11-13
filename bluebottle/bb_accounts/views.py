import uuid
from collections import namedtuple
from datetime import timedelta

from axes.utils import reset
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.http import Http404
from django.utils import timezone
from django.utils.http import base36_to_int
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import status, response, generics, parsers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.views import ObtainJSONWebTokenView

from bluebottle.bb_accounts.permissions import (
    CurrentUserPermission, IsAuthenticatedOrOpenPermission,
    SignUpTokenPermission
)
from bluebottle.bb_accounts.utils import send_welcome_mail
from bluebottle.files.views import ImageContentView
from bluebottle.initiatives.serializers import (
    MemberSerializer, CurrentMemberSerializer, AvatarImageSerializer
)
from bluebottle.members.models import AuthenticationMethod
from bluebottle.members.messages import SignUpTokenMessage, PasswordResetMessage
from bluebottle.members.models import UserActivity
from bluebottle.members.serializers import (
    PasswordResetSerializer,
    UserDataExportSerializer,
    EmailSetSerializer, PasswordUpdateSerializer, SignUpTokenSerializer,
    SignUpTokenConfirmationSerializer, UserActivitySerializer,
    CaptchaSerializer, AxesJSONWebTokenSerializer, MemberSignUpSerializer,
    PasswordStrengthSerializer, PasswordResetConfirmSerializer, AuthTokenSerializer,
    MemberProfileSerializer, AuthenticationMethodSerializer
)
from bluebottle.utils.permissions import IsCurrentUser
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.views import (
    RetrieveAPIView, JsonApiViewMixin, CreateAPIView, RetrieveUpdateDestroyAPIView
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


class AvatarImage(ImageContentView):
    queryset = USER_MODEL.objects
    field = 'avatar'
    allowed_sizes = AvatarImageSerializer.sizes


class UserActivityDetail(JsonApiViewMixin, CreateAPIView):
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)


class AuthenticationMethodList(JsonApiViewMixin, generics.ListAPIView):
    """
    List all authentication methods configured on the platform.
    Public, because the login / sign-up pages need it before a user is authenticated.
    """
    queryset = AuthenticationMethod.objects.filter(enabled=True).order_by('pk')
    serializer_class = AuthenticationMethodSerializer
    permission_classes = (AllowAny, )
    pagination_class = None

    def get_queryset(self):
        return [method for method in super().get_queryset() if method.usable]


class CurrentMemberDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveAPIView):
    """
    Retrieve details about the member
    """
    queryset = USER_MODEL.objects.all()
    serializer_class = CurrentMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, *args, **kwargs):
        return self.request.user


class MemberProfileDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateDestroyAPIView):
    """
    Retrieve details about the member
    """
    queryset = USER_MODEL.objects.all()
    serializer_class = MemberProfileSerializer
    permission_classes = [IsCurrentUser]

    def perform_destroy(self, instance):
        instance.anonymize()


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
        serializer.validated_data['is_active'] = True
        super().perform_create(serializer)


class PasswordStrengthDetail(JsonApiViewMixin, generics.CreateAPIView):
    serializer_class = PasswordStrengthSerializer

    def perform_create(self, serializer, *args, **kwargs):
        serializer.is_valid(raise_exception=True)

        model = namedtuple('Model', 'pk')
        serializer.instance = model(str(uuid.uuid4()))


class Logout(generics.CreateAPIView):
    """
    Log the user out

    """
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            self.request.user.last_logout = timezone.now()
            self.request.user.save()

        return response.Response('Logged out', status=status.HTTP_201_CREATED)


class SignUpToken(JsonApiViewMixin, CreateAPIView):
    """
    Request a signup token

    """
    permission_classes = [SignUpTokenPermission]

    queryset = USER_MODEL.objects.all()
    serializer_class = SignUpTokenSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        token = TimestampSigner().sign(instance.pk)
        if instance.accepted:
            SignUpTokenMessage(
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

        try:
            user = USER_MODEL.objects.get(pk=base36_to_int(uidb36))
        except (ValueError, OverflowError, USER_MODEL.DoesNotExist):
            raise ValidationError('Token expired')

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
    throttle_classes = [UserRateThrottle]

    def perform_create(self, serializer):
        try:
            user = USER_MODEL.objects.get(email__iexact=serializer.validated_data['email'], is_active=True)
            PasswordResetMessage(user).compose_and_send()
        except USER_MODEL.DoesNotExist:
            pass

        model = namedtuple('Model', ('pk', 'email'))
        serializer.instance = model(str(uuid.uuid4()), serializer.validated_data['email'])


class PasswordProtectedMemberCreateApiView(JsonApiViewMixin, CreateAPIView):
    permission_classes = (IsAuthenticated, )
    queryset = USER_MODEL.objects.all()

    def perform_create(self, serializer):
        user = self.request.user

        serializer.instance = user
        user.last_logout = now()

        super().perform_create(serializer)


class EmailSetView(PasswordProtectedMemberCreateApiView):
    serializer_class = EmailSetSerializer


class PasswordSetView(PasswordProtectedMemberCreateApiView):
    serializer_class = PasswordUpdateSerializer


class UserDataExport(generics.RetrieveAPIView):
    queryset = USER_MODEL.objects.all()
    serializer_class = UserDataExportSerializer

    permission_classes = (CurrentUserPermission, )

    def get_object(self):
        if isinstance(self.request.user, AnonymousUser):
            raise Http404()

        return self.request.user
