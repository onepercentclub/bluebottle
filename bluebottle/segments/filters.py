from bluebottle.grant_management.models import GrantPayout
from django.contrib import admin
from django.db.models import Q

from bluebottle.segments.models import Segment, SegmentType


def create_segment_filter(segment_type, filter_on="activity"):
    """
    Factory function to create a segment filter for a specific segment type.
    """

    class SegmentTypeFilter(admin.SimpleListFilter):
        title = segment_type.name
        parameter_name = f"segment_{segment_type.slug}"

        def lookups(self, request, model_admin):
            if filter_on == "activity":
                segments = Segment.objects.filter(
                    segment_type=segment_type,
                    segment_type__admin_activity_filter=True,
                )
            else:
                segments = Segment.objects.filter(
                    segment_type=segment_type,
                    segment_type__admin_user_filter=True,
                )
            return [(segment.id, segment.name) for segment in segments]

        def queryset(self, request, queryset):
            if self.value():
                return queryset.filter(segments__id=self.value())
            return queryset

    return SegmentTypeFilter


def segment_filter(queryset, user):
    model = queryset.model
    if user.segment_manager.count():
        if model == GrantPayout:
            return queryset.filter(
                Q(activity__segments__in=user.segment_manager.all())
            ).distinct()

        return queryset.filter(
            Q(segments__in=user.segment_manager.all())
        ).distinct()
    return queryset


class ActivitySegmentAdminMixin:
    def get_queryset(self, request):
        queryset = super(ActivitySegmentAdminMixin, self).get_queryset(request)
        queryset = segment_filter(queryset, request.user)
        return queryset

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        if not request.user.segment_manager.count() == 1:
            for segment_type in SegmentType.objects.filter(
                admin_activity_filter=True,
            ).all():
                segment_filter = create_segment_filter(segment_type)
                filters = filters + [segment_filter]
        return filters


class MemberSegmentAdminMixin:

    def get_queryset(self, request):
        queryset = super(MemberSegmentAdminMixin, self).get_queryset(request)
        if request.user.segment_manager.count():
            return queryset.filter(
                Q(segments__in=request.user.segment_manager.all())
                | Q(id=request.user.id)
            ).distinct()
        return queryset

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        if not request.user.segment_manager.count() == 1:
            for segment_type in SegmentType.objects.filter(
                admin_user_filter=True
            ).all():
                segment_filter = create_segment_filter(segment_type, "user")
                filters = filters + (segment_filter,)
        return filters
