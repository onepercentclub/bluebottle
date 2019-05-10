from django.contrib import admin
from polymorphic.admin import (
    PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter)

from bluebottle.activities.models import Activity
from bluebottle.events.models import Event
from bluebottle.funding.models import Funding
from bluebottle.jobs.models import Job


class ActivityChildAdmin(PolymorphicChildModelAdmin):
    raw_id_fields = ['owner', 'initiative']

    readonly_fields = ['status']


class ActivityAdmin(PolymorphicParentModelAdmin):
    base_model = Activity
    child_models = (Event, Funding, Job)
    list_filter = (PolymorphicChildModelFilter,)


admin.site.register(Activity, ActivityAdmin)


class ActivityAdminInline(admin.TabularInline):
    model = Activity
    readonly_fields = ['title', 'created', 'updated', 'status']
    fields = readonly_fields
    extra = 0
