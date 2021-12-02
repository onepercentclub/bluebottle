import csv

import icalendar
from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    DeleteActivityPermission, ContributorPermission
)
from bluebottle.collect.models import CollectActivity, CollectContributor, CollectType
from bluebottle.collect.serializers import (
    CollectActivitySerializer, CollectActivityTransitionSerializer, CollectContributorSerializer,
    CollectContributorTransitionSerializer, CollectTypeSerializer
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.admin import prep_field
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    RetrieveUpdateDestroyAPIView, ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView,
    JsonApiViewMixin, PrivateFileView, TranslatedApiViewMixin, RetrieveAPIView, NoPagination
)


class CollectActivityListView(JsonApiViewMixin, ListCreateAPIView):
    queryset = CollectActivity.objects.all()
    serializer_class = CollectActivitySerializer

    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
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


class CollectActivityDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
        DeleteActivityPermission
    )

    queryset = CollectActivity.objects.all()
    serializer_class = CollectActivitySerializer


class CollectActivityTransitionList(TransitionList):
    serializer_class = CollectActivityTransitionSerializer
    queryset = CollectActivity.objects.all()


class CollectActivityRelatedCollectContributorList(JsonApiViewMixin, ListAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    queryset = CollectContributor.objects.prefetch_related('user')
    serializer_class = CollectContributorSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = self.queryset.filter(
                Q(user=self.request.user) |
                Q(activity__owner=self.request.user) |
                Q(activity__initiative__activity_manager=self.request.user) |
                Q(status__in=('accepted', 'succeeded', ))
            )
        else:
            queryset = self.queryset.filter(
                status__in=('accepted', 'succeeded', )
            )

        return queryset.filter(
            activity_id=self.kwargs['activity_id']
        )


class CollectContributorList(JsonApiViewMixin, ListCreateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
    queryset = CollectContributor.objects.all()
    serializer_class = CollectContributorSerializer

    def perform_create(self, serializer):
        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )
        serializer.save(user=self.request.user)


class CollectContributorDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )
    queryset = CollectContributor.objects.all()
    serializer_class = CollectContributorSerializer


class CollectContributorTransitionList(TransitionList):
    serializer_class = CollectContributorTransitionSerializer
    queryset = CollectContributor.objects.all()


class CollectContributorExportView(PrivateFileView):
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('created', 'Registration Date'),
        ('status', 'Status'),
    )

    model = CollectActivity

    def get(self, request, *args, **kwargs):
        activity = self.get_object()

        response = HttpResponse()
        response['Content-Disposition'] = 'attachment; filename="contributors.csv"'
        response['Content-Type'] = 'text/csv'

        writer = csv.writer(response)

        row = [field[1] for field in self.fields]
        writer.writerow(row)

        for contributor in activity.contributors.instance_of(
            CollectContributor
        ):
            row = [prep_field(request, contributor, field[0]) for field in self.fields]
            writer.writerow(row)

        return response


class CollectTypeList(TranslatedApiViewMixin, JsonApiViewMixin, ListAPIView):
    serializer_class = CollectTypeSerializer
    queryset = CollectType.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = NoPagination

    def get_queryset(self):
        return super().get_queryset().order_by('translations__name')


class CollectTypeDetail(TranslatedApiViewMixin, JsonApiViewMixin, RetrieveAPIView):
    serializer_class = CollectTypeSerializer
    queryset = CollectType.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]


class CollectIcalView(PrivateFileView):
    queryset = CollectActivity.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected'],
    )

    max_age = 30 * 60  # half an hour

    def get(self, *args, **kwargs):
        instance = self.get_object()
        calendar = icalendar.Calendar()

        details = instance.description
        details += _('\nCollecting {type}').format(type=instance.type)

        event = icalendar.Event()
        event.add('summary', instance.title)
        event.add('description', details)
        event.add('url', instance.get_absolute_url())
        event.add('dtstart', instance.start)
        event.add('dtend', instance.end)
        event['uid'] = instance.uid

        organizer = icalendar.vCalAddress('MAILTO:{}'.format(instance.owner.email))
        organizer.params['cn'] = icalendar.vText(instance.owner.full_name)

        event['organizer'] = organizer
        if instance.location:
            event['location'] = icalendar.vText(instance.location.formatted_address)

        calendar.add_component(event)

        response = HttpResponse(calendar.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="%s.ics"' % (
            instance.slug
        )

        return response
