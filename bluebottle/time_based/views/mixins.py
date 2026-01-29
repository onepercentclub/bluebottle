from django.db.models import Q
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError

from bluebottle.activities.models import Activity
from bluebottle.activities.ical import ActivityIcal
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.utils.views import PrivateFileView


class AnonymizeMembersMixin:
    @property
    def owners(self):
        if 'activity_id' in self.kwargs:
            activity = Activity.objects.get(pk=self.kwargs['activity_id'])
            return activity.owners
        if 'registration_id' in self.kwargs:
            activity = Activity.objects.get(registrations__id=self.kwargs['registration_id'])
            return activity.owners
        if 'slot_id' in self.kwargs:
            activity = Activity.objects.get(slots__id=self.kwargs['slot_id'])
            return activity.owners
        return []

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['owners'] = self.owners
        context['display_member_names'] = MemberPlatformSettings.load().display_member_names

        if self.request.user and self.request.user.is_authenticated and (
            self.request.user.is_staff or
            self.request.user.is_superuser
        ):
            context['display_member_names'] = 'full_name'

        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user in self.owners
            and context['display_member_names'] == 'first_name'
        ):
            context['display_member_names'] = 'full_name'

        return context


class CreatePermissionMixin:
    def perform_create(self, serializer):
        serializer.validated_data['owner'] = self.request.user
        super().perform_create(serializer)


class FilterRelatedUserMixin:
    @property
    def owners(self):
        if 'activity_id' in self.kwargs:
            activity = Activity.objects.get(pk=self.kwargs['activity_id'])
            return list(activity.owners)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                queryset = self.queryset
            else:
                queryset = self.queryset.filter(
                    Q(user=self.request.user) |
                    Q(activity__owner=self.request.user) |
                    Q(activity__initiative__activity_manager=self.request.user) |
                    Q(status__in=('accepted', 'succeeded',))
                ).order_by('-id')
        else:
            queryset = self.queryset.filter(
                status__in=('accepted', 'succeeded',)
            ).order_by('-id')

        return queryset


class RequiredQuestionsMixin:
    def perform_create(self, serializer):
        if self.request.user.required:
            raise ValidationError('Required fields', code="required")

        serializer.validated_data['user'] = self.request.user
        super().perform_create(serializer)


class BaseSlotIcalView(PrivateFileView):

    max_age = 30 * 60  # half an hour

    def get(self, *args, **kwargs):
        instance = self.get_object()
        ical = ActivityIcal(instance)

        response = HttpResponse(ical.to_file(), content_type="text/calendar")
        response["Content-Disposition"] = 'attachment; filename="%s.ics"' % (
            instance.activity.slug
        )

        return response
