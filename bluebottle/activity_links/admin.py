from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin

from bluebottle.activity_links.models import LinkedDeed, LinkedFunding, LinkedDateActivity, LinkedActivity, \
    LinkedDateSlot, LinkedCollectCampaign, LinkedDeadlineActivity, LinkedPeriodicActivity, LinkedScheduleActivity, \
    LinkedGrantApplication


class LinkedBaseAdmin(admin.ModelAdmin):
    readonly_fields = ["title", "link", "status", "host_organization"]
    fields = readonly_fields + ['archived']


@admin.register(LinkedDeed)
class LinkedDeedAdmin(LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end']
    fields = readonly_fields + ['archived']


@admin.register(LinkedCollectCampaign)
class LinkedCollectCampaignAdmin(LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'collect_type']
    fields = readonly_fields + ['archived']


@admin.register(LinkedFunding)
class LinkedFundingAdmin(LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'target', 'donated']
    fields = readonly_fields + ['archived']


@admin.register(LinkedGrantApplication)
class LinkedGrantApplicationAdmin(LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'target']
    fields = readonly_fields


class LinkedDateSlotInline(admin.TabularInline):
    model = LinkedDateSlot
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LinkedDateActivity)
class LinkedDateActivityAdmin(LinkedBaseAdmin):
    inlines = [LinkedDateSlotInline]
    readonly_fields = LinkedBaseAdmin.readonly_fields
    fields = readonly_fields + ['archived']


@admin.register(LinkedDeadlineActivity)
class LinkedDeadlineActivityAdmin(LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'duration']
    fields = readonly_fields + ['archived']


@admin.register(LinkedPeriodicActivity)
class LinkedPeriodicActivityAdmin(LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'duration', 'period']
    fields = readonly_fields + ['archived']


@admin.register(LinkedScheduleActivity)
class LinkedScheduleActivityAdmin(LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'duration']
    fields = readonly_fields + ['archived']


@admin.register(LinkedActivity)
class LinkedActivityAdmin(PolymorphicParentModelAdmin):
    base_model = LinkedActivity
    search_fields = ['title']
    child_models = (
        LinkedDeed,
        LinkedFunding,
        LinkedGrantApplication,
        LinkedDateActivity,
        LinkedPeriodicActivity,
        LinkedDeadlineActivity,
        LinkedCollectCampaign,
        LinkedScheduleActivity
    )

    list_display = [
        'title', 'activity_type', 'status'
    ]

    def activity_type(self, obj):
        return obj.get_real_instance_class().activity_type
