from django.contrib import admin
from django.db import models
from django.forms import Textarea

from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from parler.admin import TranslatableAdmin, TranslatableStackedInline
from adminsortable.admin import SortableStackedInline
from nested_inline.admin import NestedStackedInline

from bluebottle.cms.models import Stat, Quote, ResultPage, HomePage
from bluebottle.statistics.statistics import Statistics


class StatInline(TranslatableStackedInline, NestedStackedInline, SortableStackedInline):
    model = Stat
    extra = 1
    fields = ('type', 'definition', 'title', 'value')

    readonly_fields = ['definition']

    def definition(self, obj):
        return getattr(Statistics, obj.type).__doc__


class QuoteInline(TranslatableStackedInline, NestedStackedInline):
    model = Quote
    extra = 1


class ResultPageAdmin(PlaceholderFieldAdmin, TranslatableAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    def get_prepopulated_fields(self, request, obj=None):
        # can't use `prepopulated_fields = ..` because it breaks the admin validation
        # for translated fields. This is the official django-parler workaround.
        return {
            'slug': ('title',)
        }

    list_display = 'title', 'slug', 'start_date', 'end_date'
    fields = 'title', 'slug', 'description', 'start_date', 'end_date', 'image', 'content'


class HomePageAdmin(PlaceholderFieldAdmin, TranslatableAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    fields = ('content', )


admin.site.register(ResultPage, ResultPageAdmin)
admin.site.register(HomePage, HomePageAdmin)
