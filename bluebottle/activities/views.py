import io
import qrcode
from PIL import Image, UnidentifiedImageError
from bluebottle.scim.models import SCIMPlatformSettings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.core.validators import validate_email
from django.db.models import Q, F
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import response, filters
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.filters import ActivitySearchFilter
from bluebottle.activities.models import (
    Activity, Contributor, Invite, Contribution, ActivityQuestion, ActivityAnswer, FileUploadAnswer
)
from bluebottle.activities.permissions import ActivityOwnerPermission
from bluebottle.activities.serializers import (
    ActivityLocation,
    ActivityLocationSerializer,
    ActivitySerializer,
    ActivityTransitionSerializer,
    RelatedActivityImageSerializer,
    RelatedActivityImageContentSerializer,
    ActivityPreviewSerializer,
    ActivityImageSerializer,
    ContributionSerializer,
    ActivityQuestionSerializer,
    FileUploadAnswerDocumentSerializer,
    ActivityAnswerSerializer
)
from bluebottle.activities.utils import InviteSerializer
from bluebottle.bluebottle_drf2.renderers import ElasticSearchJSONAPIRenderer
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.files.models import RelatedImage
from bluebottle.files.views import ImageContentView
from bluebottle.members.models import MemberPlatformSettings, Member
from bluebottle.notifications.models import NotificationPlatformSettings
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    ListAPIView, JsonApiViewMixin, RetrieveUpdateDestroyAPIView,
    CreateAPIView, RetrieveAPIView, JsonApiElasticSearchPagination, JsonApiPagination,
    PrivateFileView
)


class ActivityLocationList(JsonApiViewMixin, ListAPIView):
    serializer_class = ActivityLocationSerializer
    pagination_class = None
    model = Activity
    queryset = Activity.objects.all()
    permission_classes = (
        TenantConditionalOpenClose,
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user:
            type_filter = self.request.query_params.get('filter[type]')
            if (
                type_filter == 'office_subregion' and
                self.request.user.location and
                self.request.user.location.subregion

            ):
                subregion = self.request.user.location.subregion
                queryset = queryset.filter(
                    office_location__subregion=subregion
                )
            elif (
                type_filter == 'office_region' and
                self.request.user.location and
                self.request.user.location.subregion and
                self.request.user.location.subregion.region
            ):
                region = self.request.user.location.subregion.region
                queryset = queryset.filter(
                    office_location__subregion__region=region
                )

        queryset = queryset.filter(status__in=("succeeded", "open", "full", "running"))

        collects = [
            activity for activity
            in queryset.annotate(
                position=F('collectactivity__location__position'),
                location_id=F('collectactivity__location__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        periodics = [
            activity for activity
            in queryset.annotate(
                position=F('timebasedactivity__periodicactivity__location__position'),
                location_id=F('timebasedactivity__periodicactivity__location__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        deadlines = [
            activity for activity
            in queryset.annotate(
                position=F('timebasedactivity__deadlineactivity__location__position'),
                location_id=F('timebasedactivity__deadlineactivity__location__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        schedules = [
            activity for activity
            in queryset.annotate(
                position=F('timebasedactivity__scheduleactivity__location__position'),
                location_id=F('timebasedactivity__scheduleactivity__location__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        dates = [
            activity for activity
            in queryset.annotate(
                position=F('timebasedactivity__dateactivity__slots__location__position'),
                location_id=F('timebasedactivity__dateactivity__slots__location__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        fundings = [
            activity for activity
            in queryset.annotate(
                position=F('funding__initiative__place__position'),
                location_id=F('funding__initiative__place__pk')
            ).exclude(position=Point(0, 0)).filter(position__isnull=False)
        ]

        locations = list(set(
            ActivityLocation(
                pk=f'{model.JSONAPIMeta.resource_name}-{model.pk}-{model.location_id}',
                created=model.created,
                position=model.position,
                activity=model,
            ) for model in collects + dates + periodics + schedules + deadlines + fundings
        ))

        return sorted(locations, key=lambda location: location.created, reverse=True)


class ActivityPreviewList(JsonApiViewMixin, ListAPIView):
    serializer_class = ActivityPreviewSerializer
    model = Activity
    pagination_class = JsonApiElasticSearchPagination
    renderer_classes = (ElasticSearchJSONAPIRenderer,)

    def list(self, request, *args, **kwargs):
        result = self.filter_queryset(None)

        page = self.paginate_queryset(result)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(result, many=True)
        return response.Response(serializer.data)

    filter_backends = (
        ActivitySearchFilter,
    )

    permission_classes = (
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )


class ActivityList(JsonApiViewMixin, AutoPrefetchMixin, ListAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    model = Activity

    permission_classes = (
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
        'contributors': ['contributors']
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            raise PermissionError()
        return queryset.filter(
            Q(owner=user) |
            Q(initiative__owner=user) |
            Q(initiative__activity_managers=user)
        )


class ActivityDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateDestroyAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    model = Activity
    lookup_field = 'pk'

    permission_classes = (
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
        'contributors': ['contributors']
    }


class ContributionPagination(JsonApiPagination):
    page_size = 8
    max_page_size = None


class ContributionList(JsonApiViewMixin, ListAPIView):
    model = Contributor

    def get_queryset(self, *args, **kwargs):
        upcoming = self.request.query_params.get("filter[upcoming]") == "1"

        queryset = Contribution.objects.filter(
            contributor__user=self.request.user,
        ).exclude(
            contributor__status__in=['expired', 'failed'],
        ).exclude(
            effortcontribution__contribution_type='organizer',
        ).exclude(
            timecontribution__contribution_type='preparation',
        ).prefetch_related(
            'contributor',
            'contributor__activity',
            'contributor__activity__image',
            'contributor__activity__initiative',
            'contributor__activity__initiative__image',
        )
        if upcoming:
            queryset = queryset.filter(
                Q(start__gte=now())
                | Q(contributor__deadlineparticipant__status__in=['new'])
                | Q(contributor__teamscheduleparticipant__slot__status__in=['new'])
                | Q(contributor__scheduleparticipant__slot__status__in=['new'])
                | Q(contributor__periodicparticipant__status='new')
                | Q(contributor__periodicparticipant__slot__status__in=['new', 'running'])
            ).order_by("start")
        else:
            queryset = queryset.filter(
                start__lte=now(),
            ).exclude(
                contributor__scheduleparticipant__slot__status__in=['new']
            ).exclude(
                contributor__deadlineparticipant__status__in=['new']
            ).exclude(
                contributor__teamscheduleparticipant__slot__status__in=['new']
            ).exclude(
                contributor__periodicparticipant__status='new'
            ).exclude(
                contributor__periodicparticipant__slot__status__in=['new', 'running']
            ).order_by("-start")

        return queryset

    serializer_class = ContributionSerializer

    pagination_class = ContributionPagination
    permission_classes = (IsAuthenticated,)


class ParticipantCreateMixin:

    def perform_create(self, serializer):
        email = serializer.validated_data.pop('email', None)
        send_messages = serializer.validated_data.pop('send_messages', True)

        if email:
            user = Member.objects.filter(email__iexact=email).first()
            if not user:
                try:
                    validate_email(email)
                except Exception:
                    raise ValidationError(_('Not a valid email address'), code="invalid")
                member_settings = MemberPlatformSettings.load()
                scim_settings = SCIMPlatformSettings.objects.get()

                if (
                    (member_settings.closed or member_settings.confirm_signup) and
                    not scim_settings.enabled
                ):
                    try:
                        user = Member.create_by_email(email.strip())
                    except Exception:
                        raise ValidationError(_('Not a valid email address'), code="invalid")
                else:
                    raise ValidationError(_('User with email address not found'), code="not_found")
        else:
            user = self.request.user

        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )
        if not email:
            if self.request.user.required:
                raise ValidationError('Required fields', code="required")

        if self.queryset.filter(user=user, **serializer.validated_data).exists():
            raise ValidationError(_('Already participating'), code="exists")

        serializer.save(user=user, send_messages=send_messages)


class ActivityImage(ImageContentView):
    queryset = Activity.objects
    field = 'image'
    allowed_sizes = ActivityImageSerializer.sizes


class ActivityQrCode(RetrieveAPIView):

    queryset = Activity.objects

    def get(self, request, *args, **kwargs):
        notification_settings = NotificationPlatformSettings.load()
        if 'qrcode' not in notification_settings.share_options:
            return HttpResponseBadRequest('QR code sharing not enabled')
        activity = self.get_object()
        data = activity.get_absolute_url() + "?utm_source=qr_code"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        try:
            settings = SitePlatformSettings.load()
            favicon = settings.favicon
            if favicon:
                try:
                    logo = Image.open(favicon.path)
                    qr_width, qr_height = img.size
                    logo_size = qr_width // 5
                    logo.thumbnail((logo_size, logo_size), Image.LANCZOS)

                    # Create a white background and paste the logo onto it
                    if logo.mode in ("RGBA", "LA"):
                        white_bg = Image.new("RGB", logo.size, (255, 255, 255))
                        white_bg.paste(logo, mask=logo.split()[-1])
                        logo = white_bg

                    xpos = (qr_width - logo.width) // 2
                    ypos = (qr_height - logo.height) // 2

                    img.paste(logo, (xpos, ypos))
                except UnidentifiedImageError:
                    pass
        except FileNotFoundError:
            pass

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(buffer, content_type="image/png")


class RelatedActivityImageList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    def get_queryset(self):
        return RelatedImage.objects.filter(
            content_type=ContentType.objects.get_for_model(Activity)
        )

    serializer_class = RelatedActivityImageSerializer

    related_permission_classes = {
        'content_object': [
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }

    permission_classes = []


class RelatedActivityImageContent(ImageContentView):
    def get_queryset(self):
        return RelatedImage.objects.filter(
            content_type__in=[
                ContentType.objects.get_by_natural_key('time_based', 'dateactivity'),
                ContentType.objects.get_by_natural_key('time_based', 'periodactivity'),
                ContentType.objects.get_by_natural_key('funding', 'funding'),
                ContentType.objects.get_by_natural_key('assignments', 'assignment'),
                ContentType.objects.get_by_natural_key('events', 'event'),
                ContentType.objects.get_by_natural_key('deeds', 'deed'),
                ContentType.objects.get_by_natural_key('collect', 'collectactivity'),
            ]
        )

    field = 'image'
    allowed_sizes = RelatedActivityImageContentSerializer.sizes


class ActivityTransitionList(TransitionList):
    serializer_class = ActivityTransitionSerializer
    queryset = Activity.objects.all()


class InviteDetailView(JsonApiViewMixin, RetrieveAPIView):
    permission_classes = [TenantConditionalOpenClose]
    queryset = Invite.objects.all()

    serializer_class = InviteSerializer


class RelatedContributorListView(JsonApiViewMixin, ListAPIView):
    search_fields = ['user__first_name', 'user__last_name']
    filter_backends = [filters.SearchFilter]

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['display_member_names'] = MemberPlatformSettings.objects.get().display_member_names

        activity = Activity.objects.get(pk=self.kwargs['activity_id'])
        context['owners'] = [activity.owner]
        if activity.initiative:
            context['owners'] += list(activity.initiative.activity_managers.all())

        if self.request.user and self.request.user.is_authenticated and (
                self.request.user in context['owners'] or
                self.request.user.is_staff or
                self.request.user.is_superuser
        ):
            context['display_member_names'] = 'full_name'

        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                queryset = self.queryset
            else:
                queryset = self.queryset.filter(
                    Q(user=self.request.user)
                    | Q(activity__owner=self.request.user)
                    | Q(activity__initiative__activity_manager=self.request.user)
                    | Q(status__in=("accepted", "succeeded", "scheduled"))
                ).order_by("-id")
        else:
            queryset = self.queryset.filter(
                status__in=("accepted", "succeeded", "scheduled")
            ).order_by("-id")

        status = self.request.query_params.get('filter[status]')
        if status:
            queryset = queryset.filter(status__in=status.split(","))

        my = self.request.query_params.get("filter[my]")
        if my:
            if self.request.user.is_authenticated:
                queryset = queryset.filter(user=self.request.user)
            else:
                queryset = queryset.none()

        return queryset.filter(
            activity_id=self.kwargs['activity_id']
        )


class ActivityQuestionList(JsonApiViewMixin, ListAPIView):
    model = ActivityQuestion
    serializer_class = ActivityQuestionSerializer

    permission_classes = (
        TenantConditionalOpenClose,
    )

    def get_queryset(self):
        return ActivityQuestion.objects.filter(
            activity_types__contains=self.kwargs['type']
        )


class ActivityAnswerList(JsonApiViewMixin, CreateAPIView):
    queryset = ActivityAnswer.objects.all()
    serializer_class = ActivityAnswerSerializer

    permission_classes = (
        TenantConditionalOpenClose,
    )

    related_permission_classes = {
        'activity': [
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }


class ActivityAnswerDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = ActivityAnswer.objects.all()
    serializer_class = ActivityAnswerSerializer

    permission_classes = (
        TenantConditionalOpenClose,
    )

    related_permission_classes = {
        'activity': [
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }


class FileUploadAnswerDocumentView(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    relation = 'document'
    field = 'file'
    queryset = FileUploadAnswer.objects
    serializer_class = FileUploadAnswerDocumentSerializer
