from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    DeleteActivityPermission, ContributorPermission, ActivitySegmentPermission
)
from bluebottle.activities.views import RelatedContributorListView
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.deeds.serializers import (
    DeedSerializer, DeedTransitionSerializer, DeedParticipantSerializer,
    DeedParticipantTransitionSerializer
)
from bluebottle.members.models import Member, MemberPlatformSettings
from bluebottle.segments.views import ClosedSegmentActivityViewMixin
from bluebottle.time_based.permissions import CreateByEmailPermission
from bluebottle.transitions.views import TransitionList
from bluebottle.updates.permissions import IsStaffMember
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import (
    RetrieveUpdateDestroyAPIView, ListCreateAPIView, RetrieveUpdateAPIView,
    JsonApiViewMixin, ExportView, IcalView
)


class DeedListView(JsonApiViewMixin, ListCreateAPIView):
    queryset = Deed.objects.all()
    serializer_class = DeedSerializer

    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission, IsStaffMember),
    )

    def perform_create(self, serializer):
        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )
        serializer.save(owner=self.request.user)


class DeedDetailView(JsonApiViewMixin, ClosedSegmentActivityViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
        ActivitySegmentPermission,
        DeleteActivityPermission
    )

    queryset = Deed.objects.all()
    serializer_class = DeedSerializer


class DeedTransitionList(TransitionList):
    serializer_class = DeedTransitionSerializer
    queryset = Deed.objects.all()


class DeedRelatedParticipantList(RelatedContributorListView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    queryset = DeedParticipant.objects.prefetch_related('user')
    serializer_class = DeedParticipantSerializer


class ParticipantList(JsonApiViewMixin, ListCreateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
        CreateByEmailPermission
    )
    queryset = DeedParticipant.objects.all()
    serializer_class = DeedParticipantSerializer

    def perform_create(self, serializer):
        email = serializer.validated_data.pop('email', None)
        send_messages = serializer.validated_data.pop('send_messages', True)
        if email:
            user = Member.objects.filter(email__iexact=email).first()
            if not user:
                member_settings = MemberPlatformSettings.load()
                if member_settings.closed:
                    try:
                        user = Member.create_by_email(email.strip())
                    except Exception:
                        raise ValidationError(_('Not a valid email address'), code="exists")
                else:
                    raise ValidationError(_('User with email address not found'))
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

        if DeedParticipant.objects.filter(user=user, activity=serializer.validated_data['activity']).exists():
            raise ValidationError(_('Already participating'), code="exists")

        serializer.save(user=user, send_messages=send_messages)


class ParticipantDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )
    queryset = DeedParticipant.objects.all()
    serializer_class = DeedParticipantSerializer


class ParticipantTransitionList(TransitionList):
    serializer_class = DeedParticipantTransitionSerializer
    queryset = DeedParticipant.objects.all()


class ParticipantExportView(ExportView):
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('created', 'Registration Date'),
        ('status', 'Status'),
    )

    model = Deed
    filename = 'participants'

    def get_instances(self):
        return self.get_object().contributors.instance_of(
            DeedParticipant
        )


class DeedIcalView(IcalView):
    queryset = Deed.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected'],
    )
