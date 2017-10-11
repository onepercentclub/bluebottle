from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.contrib import admin
from django.db import models
from django.forms import Textarea

from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from parler.admin import TranslatableAdmin, TranslatableStackedInline
from adminsortable.admin import SortableStackedInline, NonSortableParentAdmin


from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.cms.models import SiteLinks, Link, LinkPermission, Stats, Stat, Quotes, Quote, ResultPage, Projects
from bluebottle.statistics.statistics import Statistics


class LinkPermissionAdmin(admin.ModelAdmin):
    pass


class LinkInline(TranslatableStackedInline, SortableStackedInline):
    model = Link
    raw_id_fields = ('link_permissions',)
    fields = (
        ('group', 'highlight'),
        'link_permissions',
        'title',
        ('component', 'component_id'),
        'external_link'
    )
    extra = 1


class SiteLinksAdmin(ImprovedModelForm, NonSortableParentAdmin):
    model = SiteLinks
    inlines = [LinkInline]

    def changelist_view(self, request, extra_context=None):
        # There is only one SiteLinks object per platform so redirect if users visits list view
        if self.model.objects.all().count() == 0:
            url = "admin:%s_%s_add" % (self.model._meta.app_label, self.model._meta.model_name)
            return HttpResponseRedirect(reverse(url))

        url = "admin:%s_%s_change" % (self.model._meta.app_label, self.model._meta.model_name)
        obj = self.model.objects.all()[0]
        return HttpResponseRedirect(reverse(url, args=(obj.id,)))


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
admin.site.register(SiteLinks, SiteLinksAdmin)
admin.site.register(LinkPermission, LinkPermissionAdmin)
