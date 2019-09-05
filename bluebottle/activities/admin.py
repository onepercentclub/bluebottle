from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import (
    PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter,
    StackedPolymorphicInline)

from bluebottle.activities.models import Activity
from bluebottle.events.models import Event
from bluebottle.follow.admin import FollowAdminInline
from bluebottle.funding.models import Funding
from bluebottle.assignments.models import Assignment
from bluebottle.utils.admin import FSMAdmin


class ActivityChildAdmin(PolymorphicChildModelAdmin, FSMAdmin):

    raw_id_fields = ['owner', 'initiative']
    inlines = (FollowAdminInline, )

    readonly_fields = ['status', 'created', 'updated']

    def title_display(self, obj):
        return obj.title or _('- empty -')
    title_display.short_description = _('Title')


@admin.register(Activity)
class ActivityAdmin(PolymorphicParentModelAdmin, FSMAdmin):
    base_model = Activity
    child_models = (Event, Funding, Assignment)
    readonly_fields = ['link']
    list_filter = (PolymorphicChildModelFilter, 'status', 'highlight')
    list_editable = ('highlight',)

    list_display = ['title', 'created', 'type', 'status',
                    'contribution_count', 'link', 'highlight']

    def link(self, obj):
        return format_html(u'<a href="{}" target="_blank">{}</a>', obj.get_absolute_url, obj.title)
    link.short_description = _("Show on site")

    def type(self, obj):
        return obj.get_real_instance_class().__name__


class ActivityAdminInline(StackedPolymorphicInline):
    model = Activity
    readonly_fields = ['title', 'created', 'status', 'owner']
    fields = readonly_fields
    extra = 0

    class ActivityLinkMixin(object):
        def activity_link(self, obj):
            url = reverse("admin:{}_{}_change".format(
                obj._meta.app_label,
                obj._meta.model_name),
                args=(obj.id,)
            )
            return format_html("<a href='{}'>{}</a>", url, obj.title or '-empty-')
        activity_link.short_description = _('Edit activity')

        def link(self, obj):
            return format_html('<a href="{}" target="_blank">{}</a>', obj.get_absolute_url, obj.title or '-empty-')
        link.short_description = _('View on site')

    class EventInline(StackedPolymorphicInline.Child, ActivityLinkMixin):
        readonly_fields = ['activity_link', 'link', 'start_time', 'end_time', 'status']
        fields = readonly_fields
        model = Event

    class FundingInline(StackedPolymorphicInline.Child, ActivityLinkMixin):
        readonly_fields = ['activity_link', 'link', 'target', 'deadline', 'status']
        fields = readonly_fields
        model = Funding

    class AssignmentInline(StackedPolymorphicInline.Child, ActivityLinkMixin):
        readonly_fields = ['activity_link', 'link', 'deadline', 'status']
        fields = readonly_fields
        model = Assignment

    child_inlines = (
        EventInline,
        FundingInline,
        AssignmentInline
    )
