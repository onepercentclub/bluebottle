from django.contrib import admin
from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin

from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.cms.models import Stats, Stat, Quotes, Quote, ResultPage, Projects
from django.forms import Textarea
from django.db import models


class StatInline(admin.StackedInline):
    model = Stat
    extra = 1


class StatsAdmin(ImprovedModelForm, admin.ModelAdmin):
    inlines = [StatInline]


class QuoteInline(admin.StackedInline):
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


class ResultPageAdmin(PlaceholderFieldAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }
    prepopulated_fields = {'slug': ('title',), }

    list_display = 'title', 'slug', 'start_date', 'end_date'
    fields = 'title', 'slug', 'description', 'start_date', 'end_date', 'image', 'content'


admin.site.register(Stats, StatsAdmin)
admin.site.register(Quotes, QuotesAdmin)
admin.site.register(Projects, ProjectsAdmin)
admin.site.register(ResultPage, ResultPageAdmin)
