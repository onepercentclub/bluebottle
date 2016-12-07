from django.contrib import admin
from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from parler.admin import TranslatableAdmin, TranslatableStackedInline

from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.cms.models import Stats, Stat, Quotes, Quote, ResultPage, Projects
from django.forms import Textarea
from django.db import models


class StatInline(TranslatableStackedInline):
    model = Stat
    extra = 1


class StatsAdmin(ImprovedModelForm):
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

    list_display = ('title', 'slug', 'start_date', 'end_date')
    fields = ('title', 'slug', 'description', 'image', 'start_date', 'end_date', 'content')


admin.site.register(Stats, StatsAdmin)
admin.site.register(Quotes, QuotesAdmin)
admin.site.register(Projects, ProjectsAdmin)
admin.site.register(ResultPage, ResultPageAdmin)
