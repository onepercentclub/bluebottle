from django.contrib import admin

from bluebottle.activity_links.models import LinkedDeed


@admin.register(LinkedDeed)
class LinkedDeedAdmin(admin.ModelAdmin):
    raw_id_fields = ['event', 'host_organization']
