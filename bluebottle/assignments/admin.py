from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.utils.forms import FSMModelForm


class AssignmentAdminForm(FSMModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'


class ApplicantInline(admin.TabularInline):
    model = Applicant

    raw_id_fields = ('user', )
    readonly_fields = ('time_spent', 'status', )
    extra = 0


@admin.register(Assignment)
class AssignmentAdmin(ActivityChildAdmin):
    form = AssignmentAdminForm
    inlines = (ApplicantInline, )

    base_model = Assignment

    list_editable = ('highlight',)
    list_display = ('title_display', 'created', 'status', 'highlight')

    fieldsets = (
        (_('Basic'), {'fields': (
            'title', 'slug', 'initiative', 'owner', 'status', 'transitions', 'review_status',
            'review_transitions', 'highlight'
        )}),
        (_('Details'), {'fields': (
            'description', 'capacity',
            'deadline'
        )}),
    )
