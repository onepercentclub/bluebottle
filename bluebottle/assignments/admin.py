from django.contrib import admin
from django.urls import reverse
from django.utils import translation
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget

from bluebottle.activities.admin import ActivityChildAdmin, ContributionChildAdmin
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.transitions import AssignmentTransitions, ApplicantTransitions
from bluebottle.tasks.models import Skill
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.forms import FSMModelForm
from bluebottle.wallposts.admin import WallpostInline


class AssignmentAdminForm(FSMModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


class ApplicantInline(admin.TabularInline):
    model = Applicant

    raw_id_fields = ('user', )
    readonly_fields = ('applicant', 'status', 'created', 'motivation')
    fields = ('applicant', 'user', 'time_spent', 'status', 'created', 'motivation')
    extra = 0

    can_delete = False

    def applicant(self, obj):
        url = reverse('admin:assignments_applicant_change', args=(obj.id,))
        return format_html(u'<a href="{}">{}</a>', url, obj.user.full_name)


class ApplicantAdminForm(FSMModelForm):
    class Meta:
        model = Applicant
        exclude = ['status', ]


@admin.register(Applicant)
class ApplicantAdmin(ContributionChildAdmin):
    model = Applicant
    form = ApplicantAdminForm
    list_display = ['user', 'status', 'time_spent', 'activity_link']
    raw_id_fields = ('user', 'activity')

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


class ExpertiseFilter(admin.SimpleListFilter):
    title = _('Skill')
    parameter_name = 'expertise'

    def lookups(self, request, model_admin):
        language = translation.get_language()
        return [(skill.id, skill.name) for skill in Skill.objects.language(language).order_by('translations__name')]

    def queryset(self, request, queryset):
        if self.value() is not None:
            queryset = queryset.filter(id=self.value())
        return queryset


@admin.register(Assignment)
class AssignmentAdmin(ActivityChildAdmin):
    form = AssignmentAdminForm
    inlines = (ApplicantInline, MessageAdminInline, WallpostInline)

    date_hierarchy = 'end_date'

    model = Assignment
    raw_id_fields = ('owner', 'location')

    list_display = (
        '__unicode__', 'initiative', 'created', 'status', 'highlight',
        'end_date', 'is_online', 'registration_deadline'
    )
    search_fields = ['title', 'description']
    list_filter = ['status', ExpertiseFilter, 'is_online']

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
                    form.instance.status == AssignmentTransitions.values.succeeded):
                instance.time_spent = form.instance.duration
                instance.status = ApplicantTransitions.values.succeeded
            instance.save()
        formset.save_m2m()
