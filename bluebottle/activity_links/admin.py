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


class UsedHostOrganizationListFilter(admin.SimpleListFilter):
    title = 'host organization'
    parameter_name = 'host_organization'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        organization_ids = queryset.exclude(
            host_organization__isnull=True
        ).values_list('host_organization_id', flat=True).distinct()

        organization_model = model_admin.model._meta.get_field(
            'host_organization'
        ).remote_field.model

        organizations = organization_model.objects.filter(
            pk__in=organization_ids
        ).order_by('name')

        return [(str(organization.pk), str(organization)) for organization in organizations]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(host_organization_id=self.value())
        return queryset


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
    list_filter = [UsedHostOrganizationListFilter, 'archived']
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
