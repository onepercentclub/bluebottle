from django.urls import reverse
from django.utils.html import format_html
from django_summernote.widgets import SummernoteWidget

from bluebottle.fsm.forms import StateMachineModelForm
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.admin import ActivityChildAdmin, ContributorChildAdmin
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.utils.admin import export_as_csv_action


class DeedAdminForm(StateMachineModelForm):
    class Meta(object):
        model = Deed
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


@admin.register(DeedParticipant)
class DeedParticipantAdmin(ContributorChildAdmin):
    readonly_fields = ['created']
    raw_id_fields = ['user', 'activity']
    fields = ['activity', 'user', 'status', 'states'] + readonly_fields
    list_display = ['__str__', 'activity_link', 'status']


class DeedParticipantInline(admin.TabularInline):
    model = DeedParticipant
    raw_id_fields = ['user']
    readonly_fields = ['edit', 'created', 'status']
    fields = ['edit', 'user', 'created', 'status']
    extra = 0

    def edit(self, obj):
        url = reverse('admin:deeds_deedparticipant_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, _('Edit participant'))
    edit.short_description = _('Edit participant')


@admin.register(Deed)
class DeedAdmin(ActivityChildAdmin):
    base_model = Deed
    form = DeedAdminForm
    inlines = (DeedParticipantInline,) + ActivityChildAdmin.inlines
    list_filter = ['status']
    search_fields = ['title', 'description']

    list_display = ActivityChildAdmin.list_display + [
        'start',
        'end',
        'participant_count',
    ]

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = _('Participants')

    detail_fields = ActivityChildAdmin.detail_fields + (
        'start',
        'end',
    )

    export_as_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('registration_deadline', 'Registration Deadline'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('start', 'Start'),
        ('end', 'End'),
    )

    actions = [export_as_csv_action(fields=export_as_csv_fields)]
