from django.contrib import admin
from polymorphic.admin import (
    PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter,
    StackedPolymorphicInline)

from bluebottle.activities.models import Activity
from bluebottle.events.models import Event
from bluebottle.funding.models import Funding
from bluebottle.jobs.models import Job
from bluebottle.utils.admin import ReviewAdmin


class ActivityChildAdmin(PolymorphicChildModelAdmin):
    raw_id_fields = ['owner', 'initiative']

    readonly_fields = ['status']


class ActivityAdmin(PolymorphicParentModelAdmin, ReviewAdmin):
    base_model = Activity
    child_models = (Event, Funding, Job)
    list_filter = (PolymorphicChildModelFilter,)

    list_display = ['created', 'title', 'type', 'contribution_count']

    def type(self, obj):
        return obj.get_real_instance_class().__name__


admin.site.register(Activity, ActivityAdmin)


class ActivityAdminInline(StackedPolymorphicInline):
    model = Activity
    readonly_fields = ['title', 'created', 'updated', 'status']
    fields = readonly_fields
    extra = 0

    class EventInline(StackedPolymorphicInline.Child):
        readonly_fields = ['title', 'created', 'updated']
        fields = ['status'], readonly_fields
        model = Event

    class FundingInline(StackedPolymorphicInline.Child):
        readonly_fields = ['title', 'target', 'created', 'updated']
        fields = ['status'], readonly_fields
        model = Funding

    class JobInline(StackedPolymorphicInline.Child):
        readonly_fields = ['title', 'created', 'updated']
        fields = ['status'], readonly_fields
        model = Job

    child_inlines = (
        EventInline,
        FundingInline,
        JobInline
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
