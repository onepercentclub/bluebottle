import icalendar

from django.db.models import Q
from django.http import HttpResponse
from django.utils.timezone import utc
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.activities.models import Activity

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
        context['display_member_names'] = MemberPlatformSettings.objects.get().display_member_names

        if self.request.user and self.request.user.is_authenticated and (
                self.request.user in self.owners or
                self.request.user.is_staff or
                self.request.user.is_superuser
        ):
            context['display_member_names'] = 'full_name'

        return context


class CreatePermissionMixin:
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
        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        if self.request.user.required:
            raise ValidationError('Required fields', code="required")

        serializer.save(user=self.request.user)


class BaseSlotIcalView(PrivateFileView):

    max_age = 30 * 60  # half an hour

    def get(self, *args, **kwargs):
        instance = self.get_object()
        calendar = icalendar.Calendar()

        slot = icalendar.Event()
        slot.add("summary", instance.activity.title)

        details = instance.activity.details
        if instance.is_online and instance.online_meeting_url:
            details += _("\nJoin: {url}").format(url=instance.online_meeting_url)

        slot.add("description", details)
        slot.add("url", instance.activity.get_absolute_url())
        slot.add("dtstart", instance.start.astimezone(utc))
        slot.add("dtend", (instance.start + instance.duration).astimezone(utc))
        slot["uid"] = instance.uid

        organizer = icalendar.vCalAddress(
            "MAILTO:{}".format(instance.activity.owner.email)
        )
        organizer.params["cn"] = icalendar.vText(instance.activity.owner.full_name)

        slot["organizer"] = organizer
        if instance.location:
            slot["location"] = icalendar.vText(instance.location.formatted_address)

            if instance.location_hint:
                slot["location"] = f'{slot["location"]} ({instance.location_hint})'
        calendar.add_component(slot)

        response = HttpResponse(calendar.to_ical(), content_type="text/calendar")
        response["Content-Disposition"] = 'attachment; filename="%s.ics"' % (
            instance.activity.slug
        )

        return response
