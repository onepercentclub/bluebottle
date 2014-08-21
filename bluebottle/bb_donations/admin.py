from bluebottle.utils.utils import get_model_class
from django.contrib import admin

DONATION_MODEL = get_model_class('DONATIONS_DONATION_MODEL')


class DonationAdmin(admin.ModelAdmin):
    date_hierarchy = 'updated'
    list_display = ('updated', 'project', 'user', 'amount', 'status')
    list_filter = ('status', )
    ordering = ('-updated', )
    raw_id_fields = ('user', 'project', 'fundraiser')
    readonly_fields = ('created', 'updated')
    fields = readonly_fields + ('status', 'amount', 'user', 'project', 'fundraiser')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'project__title')

admin.site.register(DONATION_MODEL, DonationAdmin)
