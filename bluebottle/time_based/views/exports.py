import re
from django.utils.timezone import now

from bluebottle.segments.models import SegmentType
from bluebottle.time_based.models import (
    DeadlineActivity,
    DeadlineParticipant,
    PeriodicActivity,
    ScheduleActivity,
    DateActivity,
    ScheduleParticipant,
    PeriodicRegistration,
    DateRegistration, RegisteredDateActivity, RegisteredDateParticipant
)
from bluebottle.utils.admin import prep_field
from bluebottle.utils.views import ExportView


class TimeBasedExportView(ExportView):
    filename = "participants"
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('created', 'Registration Date'),
        ('status', 'Status'),
        ('registration__answer', 'Registration answer'),
    )

    def get_row(self, instance):
        row = []

        for (field, name) in self.get_fields():
            if field.startswith('segment.'):
                if instance.user:
                    row.append(
                        ", ".join(
                            instance.user.segments.filter(
                                segment_type_id=field.split('.')[-1]
                            ).values_list('name', flat=True)
                        )
                    )
                else:
                    row.append('')
            else:
                row.append(prep_field(self.request, instance, field))

        return row

    def get_fields(self):
        fields = super().get_fields()

        segments = tuple(
            (f"segment.{segment.pk}", segment.name) for segment in SegmentType.objects.all()
        )
        return fields + segments

    def get_instances(self):
        return self.get_object().contributors.instance_of(
            self.participant_model
        ).prefetch_related('user__segments').select_related('user')


class DeadlineParticipantExportView(TimeBasedExportView):
    model = DeadlineActivity
    participant_model = DeadlineParticipant


class RegisteredDateParticipantExportView(TimeBasedExportView):
    model = RegisteredDateActivity
    participant_model = RegisteredDateParticipant

    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('created', 'Registration Date'),
        ('status', 'Status'),
        ('activity__start', 'Contribution Date')
    )


class ScheduleParticipantExportView(TimeBasedExportView):
    model = ScheduleActivity
    participant_model = ScheduleParticipant


class TeamScheduleParticipantExportView(TimeBasedExportView):
    model = ScheduleActivity
    fields = (
        ("user__email", "Captain email"),
        ("user__full_name", "Captain name"),
        ("created", "Registration Date"),
        ("team__status", "Status"),
        ("answer", "Registration answer"),
    )
    team_fields = (
        ("user__email", "Email"),
        ("user__full_name", "Name"),
        ("created", "Registration Date"),
        ("status", "Status"),
        ("is_captain", "Is captain"),
    )

    def get_instances(self):
        return (
            self.get_object()
            .registrations.prefetch_related("user__segments")
            .select_related("user")
        )

    def get_team_row(self, team):
        return [prep_field(self.request, team, field[0]) for field in self.team_fields]

    def get_team_data(self, team):
        return [self.get_team_row(instance) for instance in team.team_members.all()]

    def write_data(self, workbook):
        super().write_data(workbook)

        for team in self.get_object().teams.all():
            title = re.sub("[\[\]\\:*?/]", "", str(team)[:30])

            worksheet = workbook.add_worksheet(title)
            worksheet.set_column(0, 10, 30)
            worksheet.write_row(0, 0, [field[1] for field in self.team_fields])

            for index, row in enumerate(self.get_team_data(team)):
                worksheet.write_row(index + 1, 0, row)


class PeriodicParticipantExportView(TimeBasedExportView):
    model = PeriodicActivity
    participant_model = PeriodicRegistration

    fields = (
        ("user__email", "Email"),
        ("user__full_name", "Name"),
        ("created", "Registration Date"),
        ("status", "Status"),
        ("answer", "Registration answer"),
        ("total_slots", "Iterations"),
        ("total_hours", "Total hours"),
        ("first_slot__start", "First contribution"),
        ("last_slot__end", "Last contribution"),
    )

    def get_instances(self):
        return (
            self.participant_model.objects.filter(activity=self.get_object())
            .prefetch_related("user__segments")
            .select_related("user")
        )


class DateParticipantExportView(TimeBasedExportView):
    model = DateActivity
    participant_model = DateRegistration

    fields = (
        ("user__email", "Email"),
        ("user__full_name", "Name"),
        ("created", "Registration Date"),
        ("status", "Status"),
        ("answer", "Registration answer"),
    )

    def get_instances(self):
        return (
            self.participant_model.objects.filter(activity=self.get_object())
            .prefetch_related("user__segments")
            .select_related("user")
        )

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
