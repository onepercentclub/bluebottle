from datetime import datetime, time

import dateutil
import icalendar
from django.db.models import Q, ExpressionWrapper, BooleanField
from django.http import HttpResponse
from django.utils.timezone import utc, get_current_timezone, now
from django.utils.translation import gettext_lazy as _
from rest_framework import filters
from rest_framework.exceptions import ValidationError

from bluebottle.activities.models import Activity
from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    ContributorPermission, ContributionPermission, DeleteActivityPermission,
    ActivitySegmentPermission
)
from bluebottle.activities.views import RelatedContributorListView
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.models import SegmentType
from bluebottle.segments.views import ClosedSegmentActivityViewMixin
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant,
    TimeContribution,
    DateActivitySlot, SlotParticipant, Skill, TeamSlot
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
    SlotParticipantTransitionSerializer, SkillSerializer, TeamSlotSerializer, DateSlotTransitionSerializer
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.admin import prep_field
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView,
    CreateAPIView, ListAPIView, JsonApiViewMixin,
    RelatedPermissionMixin,
    PrivateFileView, ExportView, TranslatedApiViewMixin, RetrieveAPIView, JsonApiPagination
)


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
    # This view is used by activity manager when reviewing participants
    # and by the participant when viewing their own registrations e.g. My time slots
    permission_classes = [
        OneOf(ResourcePermission, ResourceOwnerPermission),
    ]

    queryset = SlotParticipant.objects.prefetch_related(
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
            activity_id = self.kwargs.get('pk', None) or self.request.GET.get('activity')
            queryset = queryset.filter(activity_id=int(activity_id))
        except (KeyError, TypeError):
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
        ordering = self.request.GET.get('ordering')
        try:
            if ordering == '-start':
                queryset = queryset.filter(
                    start__lte=dateutil.parser.parse(start).astimezone(tz)
                )
            else:
                queryset = queryset.filter(
                    start__gte=dateutil.parser.parse(start).astimezone(tz)
                )
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
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['start']


class DateSlotDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    related_permission_classes = {
        'activity': [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission)
        ]
    }
    permission_classes = [DateSlotActivityStatusPermission, ]
    queryset = DateActivitySlot.objects.all()
    serializer_class = DateActivitySlotSerializer


class TeamSlotListView(DateSlotListView):
    related_permission_classes = {
        'team.activity': [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission),
            DeleteActivityPermission
        ]
    }

    permission_classes = [TenantConditionalOpenClose]
    queryset = TeamSlot.objects.all()
    serializer_class = TeamSlotSerializer

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )
        if 'team' in serializer.validated_data:
            serializer.save(activity=serializer.validated_data['team'].activity)
        serializer.save()


class TeamSlotDetailView(DateSlotDetailView):
    permission_classes = [TenantConditionalOpenClose]
    queryset = TeamSlot.objects.all()
    serializer_class = TeamSlotSerializer


class DateActivityRelatedParticipantList(RelatedContributorListView):
    queryset = DateParticipant.objects.prefetch_related(
        'user', 'slot_participants', 'slot_participants__slot'
    )
    serializer_class = DateParticipantSerializer


class SlotRelatedParticipantList(JsonApiViewMixin, ListAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['display_member_names'] = MemberPlatformSettings.objects.get().display_member_names

        if self.request.user:
            activity = DateActivity.objects.get(slots=self.kwargs['slot_id'])

            if (
                activity.owner == self.request.user or
                self.request.user in activity.initiative.activity_managers.all() or
                self.request.user.is_staff or
                self.request.user.is_superuser
            ):
                context['display_member_names'] = 'full_name'

        return context

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        activity = DateActivity.objects.get(slots=self.kwargs['slot_id'])
        queryset = super().get_queryset(*args, **kwargs).filter(slot_id=self.kwargs['slot_id'])

        queryset = queryset.filter(participant__status='accepted')

        if user.is_anonymous:
            queryset = queryset.filter(
                status__in=('registered', 'succeeded'),
            )
        elif (
                user != activity.owner and
                user != activity.initiative.owner and
                user not in activity.initiative.activity_managers.all() and
                not user.is_staff and
                not user.is_superuser
        ):
            queryset = queryset.filter(status__in=('registered', 'succeeded'))

        return queryset

    queryset = SlotParticipant.objects.prefetch_related('participant', 'participant__user')
    serializer_class = SlotParticipantSerializer


class PeriodActivityRelatedParticipantList(RelatedContributorListView):
    queryset = PeriodParticipant.objects.prefetch_related('user')
    serializer_class = PeriodParticipantSerializer


class DateTransitionList(TransitionList):
    serializer_class = DateTransitionSerializer
    queryset = DateActivity.objects.all()


class DateSlotTransitionList(TransitionList):
    serializer_class = DateSlotTransitionSerializer
    queryset = DateActivitySlot.objects.all()


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

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['display_member_names'] = MemberPlatformSettings.objects.get().display_member_names

        if 'activity_id' in kwargs:
            activity = Activity.objects.get(pk=self.kwargs['activity_id'])
            context['owners'] = [activity.owner] + list(activity.initiative.activity_managers.all())

            if self.request.user and self.request.user.is_authenticated and (
                    self.request.user in context['owners'] or
                    self.request.user.is_staff or
                    self.request.user.is_superuser
            ):
                context['display_member_names'] = 'full_name'
        else:
            if self.request.user and self.request.user.is_authenticated and (
                    self.request.user.is_staff or
                    self.request.user.is_superuser
            ):
                context['display_member_names'] = 'full_name'

        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = self.queryset.filter(
                Q(user=self.request.user) |
                Q(activity__owner=self.request.user) |
                Q(activity__initiative__activity_manager=self.request.user) |
                Q(status__in=('accepted', 'succeeded',))
            ).annotate(
                current_user=ExpressionWrapper(
                    Q(user=self.request.user if self.request.user.is_authenticated else None),
                    output_field=BooleanField()
                )
            ).order_by('-current_user', '-id')
        else:
            queryset = self.queryset.filter(
                status__in=('accepted', 'succeeded',)
            )

        if 'activity_id' in self.kwargs:
            queryset = queryset.filter(
                activity_id=self.kwargs['activity_id']
            )
        return queryset


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

    def perform_create(self, serializer):
        slot = serializer.validated_data['slot']
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        if 'participant' in serializer.validated_data:
            participant = serializer.validated_data['participant']
            if participant.activity != slot.activity:
                raise ValidationError(_('Participant does not belong to this activity'))
        else:
            participant, _created = DateParticipant.objects.get_or_create(
                activity=slot.activity,
                user=self.request.user,
            )
        if slot.slot_participants.filter(participant__user=self.request.user).exists():
            raise ValidationError(_('Participant already registered for this slot'))
        serializer.save(participant=participant)


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

                if slot.location_hint:
                    event['location'] = f'{event["location"]} ({slot.location_hint})'

            calendar.add_component(event)

        response = HttpResponse(calendar.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="%s.ics"' % (
            instance.slug
        )
        return response


class BaseSlotIcalView(PrivateFileView):

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

            if instance.location_hint:
                slot['location'] = f'{slot["location"]} ({instance.location_hint})'
        calendar.add_component(slot)

        response = HttpResponse(calendar.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="%s.ics"' % (
            instance.activity.slug
        )

        return response


class ActivitySlotIcalView(BaseSlotIcalView):
    queryset = DateActivitySlot.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected'],
        activity__status__in=['cancelled', 'deleted', 'rejected'],
    )


class TeamSlotIcalView(BaseSlotIcalView):
    queryset = TeamSlot.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected'],
        activity__status__in=['cancelled', 'deleted', 'rejected'],
    )


class DateParticipantExportView(ExportView):
    filename = "participants"

    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('motivation', 'Motivation'),
        ('created', 'Registration Date'),
        ('status', 'Status'),
    )

    model = DateActivity

    def get_row(self, instance):
        row = []
        slots = dict(
            (str(slot_participant.slot.pk), slot_participant.status)
            for slot_participant in instance.slot_participants.all()
        )

        for (field, name) in self.get_fields():
            if field.startswith('segment.'):
                row.append(
                    ", ".join(
                        instance.user.segments.filter(
                            segment_type_id=field.split('.')[-1]
                        ).values_list('name', flat=True)
                    )
                )
            elif field.startswith('slot.'):
                row.append(slots.get(field.split('.')[-1], '-'))
            else:
                row.append(prep_field(self.request, instance, field))

        return row

    def get_fields(self):
        fields = super().get_fields()

        slots = tuple(
            (f"slot.{slot.pk}", f"{slot.title or str(slot)}\n{slot.start.strftime('%d-%m-%y %H:%M %Z')}")
            for slot in self.get_object().active_slots.order_by('start')
        )

        segments = tuple(
            (f"segment.{segment.pk}", segment.name) for segment in SegmentType.objects.all()
        )

        return fields + segments + slots

    def get_instances(self):
        return self.get_object().contributors.instance_of(
            DateParticipant
        ).prefetch_related('user__segments')


class SlotParticipantExportView(ExportView):
    filename = "participants"
    fields = (
        ('participant__user__email', 'Email'),
        ('participant__user__full_name', 'Name'),
        ('participant__motivation', 'Motivation'),
        ('created', 'Registration Date'),
        ('calculated_status', 'Status'),
    )

    model = DateActivitySlot

    def get_instances(self):
        return self.get_object().slot_participants.all()


class PeriodParticipantExportView(ExportView):
    filename = "participants"
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('motivation', 'Motivation'),
        ('created', 'Registration Date'),
        ('status', 'Status'),
    )

    model = PeriodActivity

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

    def get_fields(self):
        fields = super().get_fields()

        segments = tuple(
            (f"segment.{segment.pk}", segment.name) for segment in SegmentType.objects.all()
        )
        if InitiativePlatformSettings.objects.get().team_activities:
            fields += (('team__name', 'Team'), ('is_team_captain', 'Team Captain'))

        return fields + segments

    def get_instances(self):
        return self.get_object().contributors.instance_of(
            PeriodParticipant
        ).prefetch_related('user__segments')

    def write_data(self, workbook):
        """ Create extra tab with team info"""
        super().write_data(workbook)
        if self.get_object().team_activity == 'teams':
            worksheet = workbook.add_worksheet('Teams')

            fields = [
                ('name', 'Name'),
                ('owner__full_name', 'Owner'),
                ('id', 'ID'),
                ('status', 'Status'),
                ('accepted_participants_count', '# Accepted Participants'),
                ('slot__start', 'Start'),
                ('slot__duration', 'duration'),
            ]

            worksheet.write_row(0, 0, [field[1] for field in fields])

            for index, team in enumerate(self.get_object().teams.all()):
                row = [prep_field(self.request, team, field[0]) for field in fields]

                worksheet.write_row(index + 1, 0, row)


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
