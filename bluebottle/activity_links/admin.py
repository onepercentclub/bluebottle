from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin

from bluebottle.activity_links.models import LinkedDeed, LinkedFunding, LinkedDateActivity, LinkedActivity, \
    LinkedDateSlot, LinkedCollectCampaign, LinkedDeadlineActivity


@admin.register(LinkedDeed)
class LinkedDeedAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']


@admin.register(LinkedCollectCampaign)
class LinkedCollectCampaignAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']


@admin.register(LinkedFunding)
class LinkedFundingAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization', 'location']


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
class LinkedDateActivityAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']
    inlines = [LinkedDateSlotInline]


@admin.register(LinkedDeadlineActivity)
class LinkedDeadlineActivityAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']


@admin.register(LinkedActivity)
class LinkedActivityAdmin(PolymorphicParentModelAdmin):
    base_model = LinkedActivity
    child_models = (
        LinkedDeed,
        LinkedFunding,
        LinkedDateActivity,
        LinkedDeadlineActivity,
        LinkedCollectCampaign
    )
