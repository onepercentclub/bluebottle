from django.contrib import admin

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.jobs.models import Job, Applicant

from bluebottle.utils.forms import FSMModelForm


class JobAdminForm(FSMModelForm):
    class Meta:
        model = Job
        fields = '__all__'


class ApplicantInline(admin.TabularInline):
    model = Applicant

    raw_id_fields = ('user', )
    readonly_fields = ('time_spent', 'status', )
    extra = 0


class JobAdmin(ActivityChildAdmin):
    form = JobAdminForm
    inlines = (ApplicantInline, )

    base_model = Job


admin.site.register(Job, JobAdmin)
