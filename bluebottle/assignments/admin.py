from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.utils.admin import FSMAdmin, export_as_csv_action
from bluebottle.utils.forms import FSMModelForm


class AssignmentAdminForm(FSMModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'


class ApplicantInline(admin.TabularInline):
    model = Applicant

    raw_id_fields = ('user', )
    readonly_fields = ('applicant', 'time_spent', 'status', 'created', 'motivation')
    fields = ('applicant', 'user', 'time_spent', 'status', 'created', 'motivation')
    extra = 0

    def applicant(self, obj):
        url = reverse('admin:assignments_applicant_change', args=(obj.id,))
        return format_html(u'<a href="{}">{}</a>', url, obj.user.full_name)


class ApplicantAdminForm(FSMModelForm):
    class Meta:
        model = Applicant
        exclude = ['status', ]


@admin.register(Applicant)
class ApplicantAdmin(FSMAdmin):
    model = Applicant
    form = ApplicantAdminForm
    list_display = ['user', 'status', 'time_spent']
    raw_id_fields = ('user', 'activity')

    export_to_csv_fields = (
        ('status', 'Status'),
        ('created', 'Created'),
        ('activity', 'Activity'),
        ('owner', 'Owner'),
        ('motivation', 'Motivation'),
        ('time_spent', 'Time Spent'),
        ('document', 'Document'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]


@admin.register(Assignment)
class AssignmentAdmin(ActivityChildAdmin):
    form = AssignmentAdminForm
    inlines = (ApplicantInline, )

    base_model = Assignment
    raw_id_fields = ('owner', 'location')

    list_display = ('created', 'title', 'status', 'highlight')

    detail_fields = (
        'description',
        'capacity',
        'end_date',
        'end_date_type',
        'registration_deadline',
        'duration',
        'expertise',
        'is_online',
        'location'
    )

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('expertise', 'Expertise'),
        ('end_date_type', 'End Time Type'),
        ('end_date', 'End Date'),
        ('duration', 'Duration'),
        ('registration_deadline', 'Registration Deadline'),
        ('owner', 'Owner'),
        ('capacity', 'Capacity'),
        ('is_online', 'Will be hosted online?'),
        ('location', 'Location'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]
