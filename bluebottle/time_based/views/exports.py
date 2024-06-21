import re

from bluebottle.segments.models import SegmentType
from bluebottle.time_based.models import (
    DeadlineActivity,
    DeadlineParticipant,
    PeriodicActivity,
    ScheduleActivity,
    ScheduleParticipant,
    PeriodicRegistration,
)
from bluebottle.utils.admin import prep_field
from bluebottle.utils.views import ExportView


class TimebasedExportView(ExportView):
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
        return fields + segments

    def get_instances(self):
        return self.get_object().contributors.instance_of(
            self.participant_model
        ).prefetch_related('user__segments').select_related('user')


class DeadlineParticipantExportView(TimebasedExportView):
    model = DeadlineActivity
    participant_model = DeadlineParticipant


class ScheduleParticipantExportView(TimebasedExportView):
    model = ScheduleActivity
    participant_model = ScheduleParticipant


class TeamScheduleParticipantExportView(TimebasedExportView):
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


class PeriodicParticipantExportView(TimebasedExportView):
    model = PeriodicActivity
    participant_model = PeriodicRegistration

    fields = (
        ("user__email", "Captain Email"),
        ("user__full_name", "Captain"),
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
