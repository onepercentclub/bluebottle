from bluebottle.updates.models import Update

from bluebottle.activities.models import Contribution, Contributor, Team
from bluebottle.funding.models import Payout
from bluebottle.grant_management.models import GrantPayout
from django.contrib import admin
from django.db.models import Q

from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member
from bluebottle.segments.models import Segment
from bluebottle.time_based.models import Slot, TeamMember


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
    activity_managed_segments = user.segment_manager.filter(segment_type__admin_activity_filter=True).all()
    member_managed_segments = user.segment_manager.filter(segment_type__admin_user_filter=True).all()
    if member_managed_segments.count() and model == Member:
        segments_filter = (
            Q(segments__in=member_managed_segments) |
            Q(segments__segment_type__admin_user_filter=False)
        )
        self_filter = Q(id=user.id)
        queryset = queryset.filter(
            segments_filter | self_filter
        ).distinct()
    elif activity_managed_segments.count():
        if model == Member:
            pass
        elif model == Initiative:
            segments_filter = (
                Q(activities__segments__in=activity_managed_segments) &
                Q(activities__segments__segment_type__admin_activity_filter=True)
            )
            self_filter = Q(owner=user)
            queryset = queryset.filter(segments_filter | self_filter).distinct()
        elif model == GrantPayout:
            queryset = queryset.filter(
                (
                    Q(activity__segments__in=activity_managed_segments) &
                    Q(activity__segments__segment_type__admin_activity_filter=True)
                )
            ).distinct()
        elif issubclass(model, Contribution):
            segments_filter = (
                Q(contributor__activity__segments__in=activity_managed_segments) &
                Q(contributor__activity__segments__segment_type__admin_activity_filter=True)
            )
            self_filter = Q(contributor__activity__owner=user)
            queryset = queryset.filter(segments_filter | self_filter).distinct()
        elif model == TeamMember:
            segments_filter = (
                Q(team__activity__segments__in=activity_managed_segments) &
                Q(team__activity__segments__segment_type__admin_activity_filter=True)
            )
            self_filter = Q(team__activity__owner=user)
            queryset = queryset.filter(segments_filter | self_filter).distinct()
        elif (
                issubclass(model, Contributor)
                or issubclass(model, Slot)
                or model in [Team, Update, Payout, GrantPayout]
        ):
            segments_filter = (
                Q(activity__segments__in=activity_managed_segments) &
                Q(activity__segments__segment_type__admin_activity_filter=True)
            )
            self_filter = Q(activity__owner=user)
            queryset = queryset.filter(segments_filter | self_filter).distinct()
        else:
            queryset = queryset.filter(
                (
                    Q(segments__in=activity_managed_segments) &
                    Q(segments__segment_type__admin_activity_filter=True)
                )
            ).distinct()

    return queryset


class ActivitySegmentAdminMixin:
    def get_queryset(self, request):
        queryset = super(ActivitySegmentAdminMixin, self).get_queryset(request)
        queryset = segment_filter(queryset, request.user)
        return queryset


class MemberSegmentAdminMixin:

    def get_queryset(self, request):
        queryset = super(MemberSegmentAdminMixin, self).get_queryset(request)
        if request.user.segment_manager.count():
            return segment_filter(queryset, request.user)
        return queryset
