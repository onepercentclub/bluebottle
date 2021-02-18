from django_summernote.widgets import SummernoteWidget

from bluebottle.fsm.forms import StateMachineModelForm
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.deeds.models import Deed
from bluebottle.utils.admin import export_as_csv_action


class DeedAdminForm(StateMachineModelForm):
    class Meta(object):
        model = Deed
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


@admin.register(Deed)
class DeedAdmin(ActivityChildAdmin):
    base_model = Deed
    form = DeedAdminForm

    list_display = ActivityChildAdmin.list_display + [
        'start',
        'end',
        # 'participant_count',
    ]

    def participant_count(self, obj):
        return obj.accepted_participants.count()
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
