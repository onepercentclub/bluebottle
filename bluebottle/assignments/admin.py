from builtins import object
from django.contrib import admin
from django_summernote.widgets import SummernoteWidget

from bluebottle.activities.admin import ActivityChildAdmin, ContributionChildAdmin, ContributionInline
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.states import AssignmentStateMachine, ApplicantStateMachine
from bluebottle.fsm.admin import StateMachineFilter
from bluebottle.fsm.forms import StateMachineModelForm
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.wallposts.admin import WallpostInline


class AssignmentAdminForm(StateMachineModelForm):
    class Meta(object):
        model = Assignment
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


class ApplicantInline(ContributionInline):
    model = Applicant

    readonly_fields = ContributionInline.readonly_fields + ('time_spent', )
    fields = ContributionInline.fields + ('time_spent', )


class ApplicantAdminForm(StateMachineModelForm):
    class Meta(object):
        model = Applicant
        exclude = ('transition_date', )


@admin.register(Applicant)
class ApplicantAdmin(ContributionChildAdmin):
    model = Applicant
    form = ApplicantAdminForm
    list_display = ['user', 'state_name', 'time_spent', 'activity_link']
    raw_id_fields = ('user', 'activity')

    readonly_fields = ContributionChildAdmin.readonly_fields
    fields = ContributionChildAdmin.fields + ['time_spent', 'motivation']

    date_hierarchy = 'transition_date'

    export_to_csv_fields = (
        ('status', 'Status'),
        ('created', 'Created'),
        ('activity', 'Activity'),
        ('user__full_name', 'Owner'),
        ('user__email', 'Email'),
        ('motivation', 'Motivation'),
        ('time_spent', 'Time Spent'),
        ('document', 'Document'),
        ('contribution_date', 'Contribution Date'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]


@admin.register(Assignment)
class AssignmentAdmin(ActivityChildAdmin):
    form = AssignmentAdminForm
    inlines = (ApplicantInline, MessageAdminInline, WallpostInline)

    date_hierarchy = 'date'

    model = Assignment
    raw_id_fields = ('owner', 'location', 'initiative')

    list_display = (
        '__str__', 'initiative', 'created', 'state_name', 'highlight',
        'date', 'is_online', 'registration_deadline'
    )
    search_fields = ['title', 'description']
    list_filter = [StateMachineFilter, 'expertise', 'is_online']
    readonly_fields = ActivityChildAdmin.readonly_fields + ['local_date', ]

    detail_fields = (
        'description',
        'capacity',
        'date',
        'local_date',
        'end_date_type',
        'registration_deadline',
        'duration',
        'preparation',
        'expertise',
        'is_online',
        'location',
        'highlight',
    )

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('expertise', 'Expertise'),
        ('end_date_type', 'End Time Type'),
        ('date', 'End Date'),
        ('duration', 'Duration'),
        ('preparation', 'Preparation'),
        ('registration_deadline', 'Registration Deadline'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('capacity', 'Capacity'),
        ('is_online', 'Will be hosted online?'),
        ('location', 'Location'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            # If we created a new applicant through admin then
            # set it to succeeded when assignment is succeeded
            if (instance.__class__ == Applicant and
                    not instance.pk and
                    form.instance.status == AssignmentStateMachine.succeeded.value):
                instance.time_spent = form.instance.duration
                instance.status = ApplicantStateMachine.succeeded.value
            instance.save()
        super(AssignmentAdmin, self).save_formset(request, form, formset, change)
