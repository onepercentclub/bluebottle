from django.contrib import admin

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.events.models import Event, Participant

from bluebottle.utils.forms import FSMModelForm


class EventAdminForm(FSMModelForm):
    class Meta:
        model = Event
        fields = '__all__'


class ParticipantInline(admin.TabularInline):
    model = Participant

    raw_id_fields = ('user', )
    readonly_fields = ('time_spent', 'status', )
    extra = 0


@admin.register(Event)
class EventAdmin(ActivityChildAdmin):
    form = EventAdminForm
    inlines = (ParticipantInline, )

    base_model = Event
