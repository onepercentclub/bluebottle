from datetime import datetime, time
from django.template.defaultfilters import slugify

import dateutil
import icalendar
from django.db.models import Q
from django.http import HttpResponse
from django.utils.timezone import utc, get_current_timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    ContributorPermission, ContributionPermission, DeleteActivityPermission,
    ActivitySegmentPermission
)
from bluebottle.activities.views import RelatedContributorListView
from bluebottle.clients import properties
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.models import SegmentType
from bluebottle.segments.views import ClosedSegmentActivityViewMixin
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant,
    TimeContribution,
    DateActivitySlot, SlotParticipant, Skill
)
from bluebottle.time_based.permissions import (
    SlotParticipantPermission, DateSlotActivityStatusPermission
)
from bluebottle.time_based.serializers import (
    DateActivitySerializer,
    PeriodActivitySerializer,
    DateTransitionSerializer,
    PeriodTransitionSerializer,
    PeriodParticipantSerializer,
    DateParticipantSerializer,
    DateParticipantListSerializer,
    DateParticipantTransitionSerializer,
    PeriodParticipantTransitionSerializer,
    TimeContributionSerializer,
    DateActivitySlotSerializer,
    SlotParticipantSerializer,
    SlotParticipantTransitionSerializer, SkillSerializer
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.admin import prep_field
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView,
    CreateAPIView, ListAPIView, JsonApiViewMixin,
    PrivateFileView, TranslatedApiViewMixin, RetrieveAPIView, JsonApiPagination,
    RelatedPermissionMixin
)
from bluebottle.utils.xlsx import generate_xlsx_response


class TimeBasedActivityListView(JsonApiViewMixin, ListCreateAPIView):
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


class TimeBasedActivityDetailView(JsonApiViewMixin, ClosedSegmentActivityViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
        DeleteActivityPermission,
        ActivitySegmentPermission,
    )


class DateActivityListView(TimeBasedActivityListView):
    queryset = DateActivity.objects.all()
    serializer_class = DateActivitySerializer


class PeriodActivityListView(TimeBasedActivityListView):
    queryset = PeriodActivity.objects.all()
    serializer_class = PeriodActivitySerializer


class DateActivityDetailView(TimeBasedActivityDetailView):
    queryset = DateActivity.objects.all()
    serializer_class = DateActivitySerializer


class PeriodActivityDetailView(TimeBasedActivityDetailView):
    queryset = PeriodActivity.objects.all()
    serializer_class = PeriodActivitySerializer


class RelatedSlotParticipantListView(JsonApiViewMixin, RelatedPermissionMixin, ListAPIView):
    permission_classes = [
        OneOf(ResourcePermission, ResourceOwnerPermission),
    ]

    pagination_class = None

    queryset = SlotParticipant.objects.select_related(
        'slot', 'participant', 'participant__user'
    )
    model = DateParticipant

    def get_queryset(self, *args, **kwargs):
        participant = DateParticipant.objects.select_related(
            'activity', 'activity__initiative'
        ).get(pk=self.kwargs['participant_id'])
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated or (
            self.request.user != participant.user and
            self.request.user != participant.activity.owner and
            self.request.user != participant.activity.initiative.owner
        ):
            queryset = queryset.filter(status='registered', participant__status='accepted')

        return queryset.filter(
            participant_id=self.kwargs['participant_id']
        )

    serializer_class = SlotParticipantSerializer


class DateSlotListView(JsonApiViewMixin, ListCreateAPIView):
    related_permission_classes = {
        'activity': [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission),
            DeleteActivityPermission
        ]
    }

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        try:
            activity_id = self.request.GET['activity']
            queryset = queryset.filter(activity_id=int(activity_id))
        except KeyError:
            raise ValidationError('Missing required parameter: activity')
        except ValueError:
            raise ValidationError('Invalid parameter: activity ({})'.format(activity_id))

        try:
            contributor_id = self.request.GET['contributor']
            queryset = queryset.filter(
                slot_participants__status__in=['registered', 'succeeded'],
                slot_participants__participant_id=contributor_id
            )
        except ValueError:
            raise ValidationError('Invalid parameter: contributor ({})'.format(contributor_id))
        except KeyError:
            pass

        tz = get_current_timezone()

        start = self.request.GET.get('start')
        try:
            queryset = queryset.filter(start__gte=dateutil.parser.parse(start).astimezone(tz))
        except (ValueError, TypeError):
            pass

        end = self.request.GET.get('end')
        try:
            queryset = queryset.filter(
                start__lte=datetime.combine(dateutil.parser.parse(end), time.max).astimezone(tz)
            )
        except (ValueError, TypeError):
            pass

        return queryset

    permission_classes = [TenantConditionalOpenClose, DateSlotActivityStatusPermission, ]
    queryset = DateActivitySlot.objects.all()
    serializer_class = DateActivitySlotSerializer


class DateSlotDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    related_permission_classes = {
        'activity': [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission),
            DeleteActivityPermission
        ]
    }
    permission_classes = [DateSlotActivityStatusPermission, ]
    queryset = DateActivitySlot.objects.all()
    serializer_class = DateActivitySlotSerializer


class DateActivityRelatedParticipantList(RelatedContributorListView):
    queryset = DateParticipant.objects.prefetch_related(
        'user', 'slot_participants', 'slot_participants__slot'
    )
    serializer_class = DateParticipantSerializer


class SlotRelatedParticipantList(JsonApiViewMixin, ListAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
    pagination_class = None

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['display_member_names'] = MemberPlatformSettings.objects.get().display_member_names

        if self.request.user:
            activity = DateActivity.objects.get(slots=self.kwargs['slot_id'])

            if (
                activity.owner == self.request.user or
                self.request.user in activity.initiative.activity_managers.all()
            ):
                context['display_member_names'] = 'full_name'

        return context

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        activity = DateActivity.objects.get(slots=self.kwargs['slot_id'])
        queryset = super().get_queryset(*args, **kwargs).filter(slot_id=self.kwargs['slot_id'])

        if user.is_anonymous:
            queryset = queryset.filter(
                status__in=('registered', 'succeeded'),
                participant__status__in=('accepted', 'new'),
            )
        elif user not in (
            activity.owner,
            activity.initiative.owner,
        ):
            queryset = queryset.filter(
                Q(
                    status__in=('registered', 'succeeded'),
                    participant__status__in=('accepted', 'new'),
                ) |
                Q(participant__user=user)
            )

        return queryset

    queryset = SlotParticipant.objects.prefetch_related('participant', 'participant__user')
    serializer_class = SlotParticipantSerializer


class PeriodActivityRelatedParticipantList(RelatedContributorListView):
    queryset = PeriodParticipant.objects.prefetch_related('user')
    serializer_class = PeriodParticipantSerializer


class DateTransitionList(TransitionList):
    serializer_class = DateTransitionSerializer
    queryset = DateActivity.objects.all()


class PeriodTransitionList(TransitionList):
    serializer_class = PeriodTransitionSerializer
    queryset = PeriodActivity.objects.all()


class ParticipantList(JsonApiViewMixin, ListCreateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
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

        serializer.save(user=self.request.user)


class DateParticipantList(ParticipantList):
    queryset = DateParticipant.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DateParticipantSerializer
        else:
            return DateParticipantListSerializer


class PeriodParticipantList(ParticipantList):
    queryset = PeriodParticipant.objects.all()
    serializer_class = PeriodParticipantSerializer


class TimeContributionDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    queryset = TimeContribution.objects.all()
    serializer_class = TimeContributionSerializer
    permission_classes = [ContributionPermission]


class ParticipantDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )


class DateParticipantDetail(ParticipantDetail):
    queryset = DateParticipant.objects.all()
    serializer_class = DateParticipantSerializer


class PeriodParticipantDetail(ParticipantDetail):
    queryset = PeriodParticipant.objects.all()
    serializer_class = PeriodParticipantSerializer


class ParticipantTransitionList(TransitionList):
    pass


class DateParticipantTransitionList(ParticipantTransitionList):
    serializer_class = DateParticipantTransitionSerializer
    queryset = DateParticipant.objects.all()


class PeriodParticipantTransitionList(ParticipantTransitionList):
    serializer_class = PeriodParticipantTransitionSerializer
    queryset = PeriodParticipant.objects.all()


class SlotParticipantListView(JsonApiViewMixin, CreateAPIView):
    permission_classes = [SlotParticipantPermission]
    queryset = SlotParticipant.objects.all()
    serializer_class = SlotParticipantSerializer

    def get_queryset(self, *args, **kwargs):
        return super().queryset(*args, **kwargs).filter(
            participant__status__in=['new', 'accepted']
        )


class SlotParticipantDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = [SlotParticipantPermission]

    queryset = SlotParticipant.objects.all()
    serializer_class = SlotParticipantSerializer


class SlotParticipantTransitionList(TransitionList):
    serializer_class = SlotParticipantTransitionSerializer
    queryset = SlotParticipant.objects.all()


class ParticipantDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    queryset = DateParticipant.objects
    relation = 'document'
    field = 'file'


class DateParticipantDocumentDetail(ParticipantDocumentDetail):
    queryset = DateParticipant.objects


class PeriodParticipantDocumentDetail(ParticipantDocumentDetail):
    queryset = PeriodParticipant.objects


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

            calendar.add_component(event)

        response = HttpResponse(calendar.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="%s.ics"' % (
            instance.slug
        )
        return response


class ActivitySlotIcalView(PrivateFileView):
    queryset = DateActivitySlot.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected'],
        activity__status__in=['cancelled', 'deleted', 'rejected'],
    )

    max_age = 30 * 60  # half an hour

    def get(self, *args, **kwargs):
        instance = self.get_object()
        calendar = icalendar.Calendar()

        slot = icalendar.Event()
        slot.add('summary', instance.activity.title)

        details = instance.activity.details
        if instance.is_online and instance.online_meeting_url:
            details += _('\nJoin: {url}').format(url=instance.online_meeting_url)

        slot.add('description', details)
        slot.add('url', instance.activity.get_absolute_url())
        slot.add('dtstart', instance.start.astimezone(utc))
        slot.add('dtend', (instance.start + instance.duration).astimezone(utc))
        slot['uid'] = instance.uid

        organizer = icalendar.vCalAddress('MAILTO:{}'.format(instance.activity.owner.email))
        organizer.params['cn'] = icalendar.vText(instance.activity.owner.full_name)

        slot['organizer'] = organizer
        if instance.location:
            slot['location'] = icalendar.vText(instance.location.formatted_address)

        calendar.add_component(slot)

        response = HttpResponse(calendar.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="%s.ics"' % (
            instance.activity.slug
        )

        return response


class DateParticipantExportView(PrivateFileView):
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('motivation', 'Motivation'),
        ('created', 'Registration Date'),
        ('status', 'Status')
    )

    model = DateActivity

    def get_segment_types(self):
        return SegmentType.objects.all()

    def get(self, request, *args, **kwargs):
        activity = self.get_object()
        slots = activity.active_slots.order_by('start')
        filename = 'participants-for-{}.xlsx'.format(slugify(activity.title))
        title_row = [field[1] for field in self.fields]
        for segment_type in self.get_segment_types():
            title_row.append(segment_type.name)
        for slot in slots:
            title_row.append(
                "{}\n{}".format(slot.title or str(slot), slot.start.strftime('%d-%m-%y %H:%M %Z'))
            )
        sheet = [title_row]
        for participant in activity.contributors.instance_of(DateParticipant).prefetch_related('user__segments'):
            row = [prep_field(request, participant, field[0]) for field in self.fields]
            for segment_type in self.get_segment_types():
                segments = ", ".join(
                    participant.user.segments.filter(
                        segment_type=segment_type
                    ).values_list('name', flat=True)
                )
                row.append(segments)
            for slot in slots:
                slot_participant = slot.slot_participants.filter(participant=participant).first()
                if slot_participant:
                    row.append(slot_participant.status)
                else:
                    row.append('-')
            sheet.append(row)

        return generate_xlsx_response(filename=filename, data=sheet)


class PeriodParticipantExportView(PrivateFileView):
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('motivation', 'Motivation'),
        ('created', 'Registration Date'),
        ('status', 'Status')
    )

    model = PeriodActivity

    def get_segment_types(self):
        return SegmentType.objects.all()

    def get(self, request, *args, **kwargs):
        activity = self.get_object()
        filename = 'participants-for-{}.xlsx'.format(slugify(activity.title))

        sheet = []
        title_row = [field[1] for field in self.fields]
        for segment_type in self.get_segment_types():
            title_row.append(segment_type.name)
        sheet.append(title_row)

        for t, participant in enumerate(
            activity.contributors.instance_of(PeriodParticipant).prefetch_related('user__segments')
        ):
            row = [prep_field(request, participant, field[0]) for field in self.fields]
            for segment_type in self.get_segment_types():
                segments = ", ".join(
                    participant.user.segments.filter(
                        segment_type=segment_type
                    ).values_list('name', flat=True)
                )
                row.append(segments)
            sheet.append(row)

        return generate_xlsx_response(filename=filename, data=sheet)


class SkillPagination(JsonApiPagination):
    page_size = 100


class SkillList(TranslatedApiViewMixin, JsonApiViewMixin, ListAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = SkillPagination

    def get_queryset(self):
        lang = self.request.LANGUAGE_CODE or properties.LANGUAGE_CODE
        return super().get_queryset().translated(lang).order_by('translations__name')


class SkillDetail(TranslatedApiViewMixin, JsonApiViewMixin, RetrieveAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
