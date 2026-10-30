from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from bluebottle.activities.models import Activity
from bluebottle.activities.permissions import RelatedActivityOwnerPermission
from bluebottle.notifications.models import ActivityMessageTemplate
from bluebottle.notifications.previews import get_message_previews
from bluebottle.notifications.serializers import (
    ActivityMessageDefaultSerializer, ActivityMessageTemplateSerializer
)
from bluebottle.utils.views import (
    JsonApiViewMixin,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)


class ActivityMessageTemplateMixin:
    queryset = ActivityMessageTemplate.objects.prefetch_related('activity').order_by('pk')
    serializer_class = ActivityMessageTemplateSerializer
    permission_classes = (RelatedActivityOwnerPermission,)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return queryset

        return queryset.filter(
            Q(activity__owner=user) |
            Q(activity__initiative__owner=user) |
            Q(activity__initiative__activity_managers=user)
        ).distinct()


class ActivityMessageTemplateList(ActivityMessageTemplateMixin, JsonApiViewMixin, ListCreateAPIView):
    def get_queryset(self):
        queryset = super().get_queryset()
        activity_id = self.request.query_params.get('filter[activity]')
        if activity_id:
            queryset = queryset.filter(activity_id=activity_id)
        return queryset


class ActivityMessageTemplateDetail(ActivityMessageTemplateMixin, JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    pass


class RelatedActivityMessageTemplateList(ActivityMessageTemplateMixin, JsonApiViewMixin, ListAPIView):
    def get_queryset(self):
        return super().get_queryset().filter(activity_id=self.kwargs['activity_id'])


class ActivityMessageDefaultList(JsonApiViewMixin, generics.ListAPIView):
    serializer_class = ActivityMessageDefaultSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    resource_name = 'activity-message-defaults'

    def get_queryset(self):
        activity = get_object_or_404(
            Activity, pk=self.request.query_params.get('filter[activity]')
        )
        user = self.request.user
        if not (user.is_staff or user.is_superuser or user in activity.owners):
            raise PermissionDenied()
        return get_message_previews(activity)
