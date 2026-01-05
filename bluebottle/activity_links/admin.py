from django.contrib import admin

from bluebottle.activity_links.models import LinkedDeed, LinkedFunding, LinkedDateActivity


@admin.register(LinkedDeed)
class LinkedDeedAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']


@admin.register(LinkedFunding)
class LinkedFundingAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']


@admin.register(LinkedDateActivity)
class LinkedDateActivityAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']
