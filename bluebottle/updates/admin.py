
from django.contrib import admin
from bluebottle.updates.models import Update


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    pass
