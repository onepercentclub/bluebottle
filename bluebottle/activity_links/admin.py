from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin

from bluebottle.activity_links.models import LinkedDeed, LinkedFunding, LinkedDateActivity, LinkedActivity


@admin.register(LinkedDeed)
class LinkedDeedAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']


@admin.register(LinkedFunding)
class LinkedFundingAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization', 'location']


@admin.register(LinkedDateActivity)
class LinkedDateActivityAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']


@admin.register(LinkedActivity)
class LinkedActivityAdmin(PolymorphicParentModelAdmin):
    base_model = LinkedActivity
    child_models = (LinkedDeed, LinkedFunding, LinkedDateActivity)
