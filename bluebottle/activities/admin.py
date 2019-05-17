from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import (
    PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter,
    StackedPolymorphicInline)

from bluebottle.activities.models import Activity
from bluebottle.events.models import Event
from bluebottle.funding.models import Funding
from bluebottle.jobs.models import Job
from bluebottle.utils.admin import FSMAdmin


class ActivityChildAdmin(PolymorphicChildModelAdmin):
    raw_id_fields = ['owner', 'initiative']

    readonly_fields = ['status']


@admin.register(Activity)
class ActivityAdmin(PolymorphicParentModelAdmin, FSMAdmin):
    fsm_field = 'status'
    base_model = Activity
    child_models = (Event, Funding, Job)
    list_filter = (PolymorphicChildModelFilter,)

    list_display = ['created', 'title', 'type', 'contribution_count']

    def type(self, obj):
        return obj.get_real_instance_class().__name__


class ActivityAdminInline(StackedPolymorphicInline):
    model = Activity
    readonly_fields = ['title', 'created', 'status']
    fields = readonly_fields
    extra = 0

    class ActivityLinkMixin(object):
        def activity_link(self, obj):
            url = reverse("admin:{}_{}_change".format(
                obj._meta.app_label,
                obj._meta.model_name),
                args=(obj.id,)
            )
            return format_html("<a href='{}'>{}</a>", url, obj.title)
        activity_link.short_description = _('Activity')

    class EventInline(StackedPolymorphicInline.Child, ActivityLinkMixin):
        readonly_fields = ['activity_link', 'start', 'status']
        fields = readonly_fields
        model = Event

    class FundingInline(StackedPolymorphicInline.Child, ActivityLinkMixin):
        readonly_fields = ['activity_link', 'target', 'deadline', 'status']
        fields = readonly_fields
        model = Funding

    class JobInline(StackedPolymorphicInline.Child, ActivityLinkMixin):
        readonly_fields = ['activity_link', 'start', 'status']
        fields = readonly_fields
        model = Job

    child_inlines = (
        EventInline,
        FundingInline,
        # FIXME: This throws an error. Dunno why...
        # JobInline
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
