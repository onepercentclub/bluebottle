from django.contrib import admin
from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin

from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.cms.models import Stats, Stat, Quotes, Quote, ResultPage


class StatInline(admin.StackedInline):
    model = Stat
    extra = 1


class StatsAdmin(ImprovedModelForm, admin.ModelAdmin):
    inlines = [StatInline]


class QuoteInline(admin.StackedInline):
    model = Quote
    extra = 1


class QuotesAdmin(ImprovedModelForm, admin.ModelAdmin):
    inlines = [QuoteInline]


class ResultPageAdmin(PlaceholderFieldAdmin):
    prepopulated_fields = {'slug': ('title',), }

    list_display = 'title', 'slug', 'start_date', 'end_date'
    fields = 'title', 'slug', 'description', 'start_date', 'end_date', 'content'


admin.site.register(Stats, StatsAdmin)
admin.site.register(Quotes, QuotesAdmin)
admin.site.register(ResultPage, ResultPageAdmin)
