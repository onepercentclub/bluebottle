import re

import icalendar
from django.http import HttpResponse
from django.utils.timezone import utc, get_current_timezone, now
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.permissions import (
    ContributionPermission
)
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.models import SegmentType
from bluebottle.time_based.models import (
    DateActivity,
    DateParticipant,
    TimeContribution,
    DateActivitySlot, Skill, DateRegistration
)
from bluebottle.time_based.permissions import (
    DateParticipantPermission
)
from bluebottle.time_based.serializers import (
    DateTransitionSerializer,
    TimeContributionSerializer,
    DateParticipantSerializer,
    DateParticipantTransitionSerializer, SkillSerializer, DateSlotTransitionSerializer, DateRegistrationSerializer,
)
from bluebottle.time_based.views import RelatedRegistrationListView
from bluebottle.time_based.views.mixins import BaseSlotIcalView
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.admin import prep_field
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView,
    ListAPIView, JsonApiViewMixin,
    RelatedPermissionMixin,
    PrivateFileView, ExportView, TranslatedApiViewMixin, RetrieveAPIView, JsonApiPagination
)


class OldRelatedSlotParticipantListView(JsonApiViewMixin, RelatedPermissionMixin, ListAPIView):
    # This view is used by activity manager when reviewing participants
    # and by the participant when viewing their own registrations e.g. My time slots
    permission_classes = [
        OneOf(ResourcePermission, ResourceOwnerPermission),
    ]

    queryset = DateParticipant.objects.prefetch_related(
        'slot', 'participant', 'participant__user'
    )

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        show_past = self.request.GET.get('past', None)

        participant = DateParticipant.objects.select_related(
            'activity', 'activity__initiative',
        ).get(pk=self.kwargs['participant_id'])

        if not self.request.user.is_authenticated or (
            self.request.user != participant.user and
            self.request.user != participant.activity.owner and
            self.request.user != participant.activity.initiative.owner
        ):
            queryset = queryset.filter(participant__status='accepted')
            queryset = queryset.filter(status='registered')

        if show_past == '1':
            queryset = queryset.order_by('-slot__start')
            queryset = queryset.filter(slot__start__lte=now())
        elif show_past == '0':
            queryset = queryset.order_by('slot__start')
            queryset = queryset.filter(slot__start__gte=now())
        else:
            queryset = queryset.order_by('slot__start')

        return queryset.filter(
            participant=participant
        )

    serializer_class = DateParticipantSerializer


class DateActivityRelatedRegistrationList(RelatedRegistrationListView):
    queryset = DateRegistration.objects.prefetch_related(
        'user', 'participants', 'participants__slot'
    )
    serializer_class = DateRegistrationSerializer


class DateTransitionList(TransitionList):
    serializer_class = DateTransitionSerializer
    queryset = DateActivity.objects.all()


class DateSlotTransitionList(TransitionList):
    serializer_class = DateSlotTransitionSerializer
    queryset = DateActivitySlot.objects.all()


class TimeContributionDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    queryset = TimeContribution.objects.all()
    serializer_class = TimeContributionSerializer
    permission_classes = [ContributionPermission]


class SlotParticipantDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = [DateParticipantPermission]

    queryset = DateParticipant.objects.all()
    serializer_class = DateParticipantSerializer


class SlotParticipantTransitionList(TransitionList):
    serializer_class = DateParticipantTransitionSerializer
    queryset = DateParticipant.objects.all()


class DateActivityIcalView(PrivateFileView):
    queryset = DateActivity.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected']
    )

    max_age = 30 * 60  # half an hour

    def get(self, *args, **kwargs):
        instance = super(DateActivityIcalView, self).get_object()
        calendar = icalendar.Calendar()
        slots = instance.slots.filter(
            status__in=['open', 'full', 'finished'],
        )
        if kwargs.get('user_id'):
            slots = slots.filter(slot_participants__participant__user__id=kwargs['user_id'])

        for slot in slots:
            event = icalendar.Event()
            event.add('summary', instance.title)

            details = instance.details
            if slot.is_online and slot.online_meeting_url:
                details += _('\nJoin: {url}').format(url=slot.online_meeting_url)

            event.add('description', details)
            event.add('url', instance.get_absolute_url())
            event.add('dtstart', slot.start.astimezone(utc))
            event.add('dtend', (slot.start + slot.duration).astimezone(utc))
            event['uid'] = slot.uid

            organizer = icalendar.vCalAddress('MAILTO:{}'.format(instance.owner.email))
            organizer.params['cn'] = icalendar.vText(instance.owner.full_name)

            event['organizer'] = organizer
            if slot.location:
                event['location'] = icalendar.vText(slot.location.formatted_address)

                if slot.location_hint:
                    event['location'] = f'{event["location"]} ({slot.location_hint})'

            calendar.add_component(event)

        response = HttpResponse(calendar.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="%s.ics"' % (
            instance.slug
        )
        return response


class ActivitySlotIcalView(BaseSlotIcalView):
    queryset = DateActivitySlot.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected'],
        activity__status__in=['cancelled', 'deleted', 'rejected'],
    )


class DateParticipantExportView(ExportView):
    filename = "participants"

    def get_fields(self):
        question = self.get_object().review_title
        fields = (
            ('participant__user__email', 'Email'),
            ('participant__user__full_name', 'Name'),
            ('created', 'Registration Date'),
            ('calculated_status', 'Status'),
        )
        if question:
            fields += (
                ('participant__motivation', question),
            )

        segments = tuple(
            (f"segment.{segment.pk}", segment.name) for segment in SegmentType.objects.all()
        )

        return fields + segments

    model = DateActivity

    def get_row(self, instance):
        row = []

        for (field, name) in self.get_fields():
            if field.startswith('segment.'):
                row.append(
                    ", ".join(
                        instance.user.segments.filter(
                            segment_type_id=field.split('.')[-1]
                        ).values_list('name', flat=True)
                    )
                )
            else:
                row.append(prep_field(self.request, instance, field))

        return row

    def write_data(self, workbook):
        activity = self.get_object()
        bold = workbook.add_format({'bold': True})
        if activity.status == 'succeeded':
            slots = activity.slots.order_by('start')
        else:
            slots = activity.active_slots.filter(start__gt=now()).order_by('start')
        for slot in slots:
            title = f"{slot.start.strftime('%d-%m-%y %H:%M')} {slot.id} {slot.title or ''}"
            title = re.sub("[\[\]\\:*?/]", '', str(title)[:30])
            worksheet = workbook.add_worksheet(title)
            worksheet.set_column(0, 4, 30)
            c = 0
            for field in self.get_fields():
                worksheet.write(0, c, field[1], bold)
                c += 1
            r = 0

            for participant in slot.slot_participants.all():
                row = self.get_row(participant)
                r += 1
                worksheet.write_row(r, 0, row)

    def get_instances(self):
        return self.get_object().contributors.instance_of(
            DateParticipant
        ).prefetch_related('user__segments')


class SlotParticipantExportView(ExportView):
    filename = "participants"

    model = DateActivitySlot

    def get_instances(self):
        return self.get_object().slot_participants.all()

    def get_fields(self):
        question = self.get_object().activity.review_title
        fields = (
            ('participant__user__email', 'Email'),
            ('participant__user__full_name', 'Name'),
            ('created', 'Registration Date'),
            ('calculated_status', 'Status'),
        )
        if question:
            fields += (
                ('participant__motivation', question),
            )
        return fields


class SkillPagination(JsonApiPagination):
    page_size = 100


class SkillList(TranslatedApiViewMixin, JsonApiViewMixin, ListAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = SkillPagination


class SkillDetail(TranslatedApiViewMixin, JsonApiViewMixin, RetrieveAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
