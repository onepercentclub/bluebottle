from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.utils.admin import FSMAdmin
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


@admin.register(Assignment)
class AssignmentAdmin(ActivityChildAdmin):
    form = AssignmentAdminForm
    inlines = (ApplicantInline, )

    base_model = Assignment
    raw_id_fields = ('owner', 'location')

    list_display = ('title_display', 'created', 'status', 'highlight')

    fieldsets = (
        (_('Basic'), {'fields': (
            'title', 'slug', 'initiative', 'owner', 'status', 'transitions', 'review_status',
            'review_transitions', 'highlight', 'stats_data'
        )}),
        (_('Details'), {'fields': (
            'description', 'capacity',
            'end_date', 'end_date_type',
            'registration_deadline',
            'duration', 'expertise',
            'is_online', 'location'
        )}),
    )
