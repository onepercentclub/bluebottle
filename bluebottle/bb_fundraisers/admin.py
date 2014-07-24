from django.contrib import admin
from django.utils import translation

from babel.numbers import format_currency
from bluebottle.utils.utils import get_model_class

FUNDRAISER_MODEL = get_model_class('FUNDRAISERS_FUNDRAISER_MODEL')

class FundRaiserAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount_override', 'deadline', 'amount_donated_override')
    raw_id_fields = ('project', 'owner')

    search_fields = ('title', 'project__title')


    def amount_override(self, obj):
        language = translation.get_language().split('-')[0]
        return format_currency(obj.amount / 100.0, obj.currency, locale=language)

    amount_override.short_description = 'amount'

    def amount_donated_override(self, obj):
        language = translation.get_language().split('-')[0]
        return format_currency(int(obj.amount) / 100.0, obj.currency, locale=language)

    amount_donated_override.short_description = 'amount donated'

admin.site.register(FUNDRAISER_MODEL, FundRaiserAdmin)