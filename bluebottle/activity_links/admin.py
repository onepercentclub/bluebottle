from bluebottle.activity_links.models import LinkedDeed
from django.contrib import admin


@admin.register(LinkedDeed)
class LinkedDeedAdmin(admin.ModelAdmin):
    pass
