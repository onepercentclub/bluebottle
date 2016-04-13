from django.contrib import admin

from bluebottle.statistics.models import Statistic
# from modeltranslation.admin import TranslationAdmin

class StatisticAdmin(admin.ModelAdmin):
    model = Statistic
    list_editable = ('sequence', )
    list_display_links = ('title',)
    list_display = ('sequence', 'title', 'type', 'calculated_value')

    readonly_fields = ('calculated_value', )

admin.site.register(Statistic, StatisticAdmin)