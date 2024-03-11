from bluebottle.segments.models import SegmentType
from bluebottle.time_based.models import (
    DeadlineActivity,
    DeadlineParticipant,
    PeriodicActivity,
    PeriodicParticipant,
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


class PeriodicParticipantExportView(TimebasedExportView):
    model = PeriodicActivity
    participant_model = PeriodicParticipant
