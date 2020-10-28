from datetime import timedelta

from bluebottle.members.models import CustomMemberFieldSettings
from .exporter import ExportModelResource
from ..impact.models import ImpactType
from ..segments.models import SegmentType


class ImpactMixin:

    def get_extra_fields(self):
        return super().get_extra_fields() + tuple([
            (f"impact:{impact.slug}", impact.name)
            for impact in ImpactType.objects.filter(active=True).all()
        ])


class SegmentMixin:

    def get_extra_fields(self):
        return super().get_extra_fields() + tuple([
            (f"segment:{segment.slug}", segment.name)
            for segment in SegmentType.objects.filter(is_active=True).all()
        ])


class DateRangeResource(ExportModelResource):
    range_field = 'created'
    select_related = None

    def get_queryset(self):
        qs = super().get_queryset()
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        frm, to = self.kwargs.get('from_date'), self.kwargs.get('to_date')
        to = to + timedelta(days=1)
        return qs.filter(**{'%s__range' % self.range_field: (frm, to)})


class UserResource(SegmentMixin, DateRangeResource):
    range_field = 'date_joined'
    select_related = ('location', 'location__group')

    def get_queryset(self):
        return super().get_queryset().exclude(email='devteam+accounting@onepercentclub.com')

    def get_extra_fields(self):
        return super().get_extra_fields() + tuple([
            (f"extra_{extra.name}", extra.description)
            for extra in CustomMemberFieldSettings.objects.all()
        ])


class InitiativeResource(DateRangeResource):
    select_related = (
        'owner', 'location', 'place',
    )


class AssignmentResource(ImpactMixin, SegmentMixin, DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class ApplicantResource(DateRangeResource):
    select_related = (
        'activity', 'user'
    )

    def get_extra_fields(self):
        return tuple([
            (f"user__extra_{extra.name}", extra.description)
            for extra in CustomMemberFieldSettings.objects.all()
        ])


class EventResource(ImpactMixin, SegmentMixin, DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class ParticipantResource(DateRangeResource):
    select_related = (
        'activity', 'user'
    )

    def get_extra_fields(self):
        return tuple([
            (f"user__extra_{extra.name}", extra.description)
            for extra in CustomMemberFieldSettings.objects.all()
        ])


class FundingResource(ImpactMixin, SegmentMixin, DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class DonationResource(DateRangeResource):
    select_related = (
        'activity', 'user'
    )

    def get_extra_fields(self):
        return tuple([
            (f"user__extra_{extra.name}", extra.description)
            for extra in CustomMemberFieldSettings.objects.all()
        ])
