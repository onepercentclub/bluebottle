import re
from datetime import datetime, time

import dateutil
import icalendar
from django.core.validators import validate_email
from django.db.models import Q, ExpressionWrapper, BooleanField
from django.http import HttpResponse
from django.utils.timezone import utc, get_current_timezone, now
from django.utils.translation import gettext_lazy as _
from rest_framework import filters
from rest_framework.exceptions import ValidationError

from bluebottle.activities.models import Activity
from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityStatusPermission,
    ContributorPermission, ContributionPermission, DeleteActivityPermission,
)
from bluebottle.activities.views import RelatedContributorListView
from bluebottle.members.models import MemberPlatformSettings, Member
from bluebottle.segments.models import SegmentType
from bluebottle.time_based.models import (
    DateActivity,
    DateParticipant,
    TimeContribution,
    DateActivitySlot, SlotParticipant, Skill
)
from bluebottle.time_based.permissions import (
    SlotParticipantPermission, DateSlotActivityStatusPermission, CreateByEmailPermission
)
from bluebottle.time_based.serializers import (
    DateTransitionSerializer,
    DateParticipantSerializer,
    DateParticipantListSerializer,
    DateParticipantTransitionSerializer,
    TimeContributionSerializer,
    DateActivitySlotSerializer,
    SlotParticipantSerializer,
    SlotParticipantTransitionSerializer, SkillSerializer, DateSlotTransitionSerializer,
)
from bluebottle.time_based.views.mixins import BaseSlotIcalView
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
                self.request.user in activity.owners or
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
            user not in activity.owners and
            not user.is_staff and
            not user.is_superuser
        ):
            queryset = queryset.filter(status__in=('registered', 'succeeded'))

        return queryset

    queryset = SlotParticipant.objects.prefetch_related('participant', 'participant__user')
    serializer_class = SlotParticipantSerializer


class DateTransitionList(TransitionList):
    serializer_class = DateTransitionSerializer
    queryset = DateActivity.objects.all()


class DateSlotTransitionList(TransitionList):
    serializer_class = DateSlotTransitionSerializer
    queryset = DateActivitySlot.objects.all()


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
            context['owners'] = list(activity.owners)

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


class ParticipantTransitionList(TransitionList):
    pass


class DateParticipantTransitionList(ParticipantTransitionList):
    serializer_class = DateParticipantTransitionSerializer
    queryset = DateParticipant.objects.all()


class SlotParticipantListView(JsonApiViewMixin, CreateAPIView):
    permission_classes = [
        SlotParticipantPermission,
        CreateByEmailPermission
    ]
    queryset = SlotParticipant.objects.all()
    serializer_class = SlotParticipantSerializer

    def get_queryset(self, *args, **kwargs):
        return super().queryset(*args, **kwargs).filter(
            participant__status__in=['new', 'accepted']
        )

    def perform_create(self, serializer):
        slot = serializer.validated_data['slot']
        email = serializer.validated_data.pop('email', None)
        send_messages = serializer.validated_data.pop('send_messages', True)
        if email:
            user = Member.objects.filter(email__iexact=email).first()
            if not user:
                try:
                    validate_email(email)
                except Exception:
                    raise ValidationError(_('Not a valid email address'), code="invalid")
                member_settings = MemberPlatformSettings.load()
                if member_settings.closed or member_settings.confirm_signup:
                    try:
                        user = Member.create_by_email(email.strip())
                    except Exception:
                        raise ValidationError(_('Not a valid email address'), code="exists")
                else:
                    raise ValidationError(_('User with email address not found'))

        else:
            user = self.request.user

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
                user=user,
            )
        if slot.slot_participants.filter(participant__user=user).exists():
            raise ValidationError(_('Participant already registered for this slot'))

        serializer.save(participant=participant, send_messages=send_messages)


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
