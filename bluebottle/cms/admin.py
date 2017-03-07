from django.contrib import admin
from django.db import models
from django.forms import Textarea

from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from parler.admin import TranslatableAdmin, TranslatableStackedInline
from adminsortable.admin import SortableStackedInline, NonSortableParentAdmin


from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.cms.models import Stats, Stat, Quotes, Quote, ResultPage, Projects
from bluebottle.statistics.statistics import Statistics


class StatInline(TranslatableStackedInline, SortableStackedInline):
    model = Stat
    extra = 1

    readonly_fields = ['definition']

    def definition(self, obj):
        return getattr(Statistics, obj.type).__doc__


class StatsAdmin(ImprovedModelForm, NonSortableParentAdmin):
    inlines = [StatInline]


class QuoteInline(TranslatableStackedInline):
    model = Quote
    extra = 1


class ProjectInline(admin.StackedInline):
    model = Projects.projects.through
    raw_id_fields = ('project', )
    extra = 1


class QuotesAdmin(ImprovedModelForm, admin.ModelAdmin):
    inlines = [QuoteInline]


class ProjectsAdmin(ImprovedModelForm, admin.ModelAdmin):
    inlines = [ProjectInline]
    exclude = ('projects', )


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


admin.site.register(Stats, StatsAdmin)
admin.site.register(Quotes, QuotesAdmin)
admin.site.register(Projects, ProjectsAdmin)
admin.site.register(ResultPage, ResultPageAdmin)
