from django.core.urlresolvers import reverse
from django.contrib import admin
from django.db import models
from django.forms import Textarea
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_singleton_admin.admin import SingletonAdmin

from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from parler.admin import TranslatableAdmin, TranslatableStackedInline
from adminsortable.admin import SortableStackedInline, NonSortableParentAdmin, SortableTabularInline

from bluebottle.common.admin_utils import ImprovedModelForm
from bluebottle.cms.models import (
    SiteLinks, Link, LinkGroup, LinkPermission, Stats, Stat, Quotes, Quote, ResultPage, Projects
)
from bluebottle.statistics.statistics import Statistics


class LinkPermissionAdmin(admin.ModelAdmin):
    model = LinkPermission

    def get_model_perms(self, request):
        return {}


class LinkInline(SortableStackedInline):
    model = Link
    extra = 0

    fields = (
        ('title', 'highlight'),
        'link_permissions',
        ('component', 'component_id'),
        'external_link',

    )


class LinkGroupAdmin(NonSortableParentAdmin):
    model = LinkGroup
    inlines = [LinkInline]

    def get_model_perms(self, request):
        return {}

    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse('admin:cms_sitelinks_change', args=(obj.site_links_id, )))

    def response_change(self, request, obj):
        return redirect(reverse('admin:cms_sitelinks_change', args=(obj.site_links_id, )))


class LinkGroupInline(SortableTabularInline):
    model = LinkGroup
    readonly_fields = ('title', 'edit_url',)
    fields = ('name', 'title', 'edit_url', )
    extra = 0

    def edit_url(self, obj):
        url = ''

        if obj.id is not None:
            url = "admin:%s_%s_change" % (self.model._meta.app_label,
                                          self.model._meta.model_name)
            return format_html(
                u"<a href='{}'>{}</a>",
                str(reverse(url, args=(obj.id,))), _('Edit this group')
            )
        return _('First save to edit this group')
    edit_url.short_name = 'Edit group'


class SiteLinksAdmin(NonSortableParentAdmin):
    model = SiteLinks
    inlines = [LinkGroupInline]


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


from bluebottle.cms.models import SiteContentSettings


class SiteContentSettingsAdmin(SingletonAdmin):
    pass


admin.site.register(Stats, StatsAdmin)
admin.site.register(Quotes, QuotesAdmin)
admin.site.register(Projects, ProjectsAdmin)
admin.site.register(ResultPage, ResultPageAdmin)
admin.site.register(SiteLinks, SiteLinksAdmin)
admin.site.register(LinkGroup, LinkGroupAdmin)
admin.site.register(LinkPermission, LinkPermissionAdmin)
admin.site.register(SiteContentSettings, SiteContentSettingsAdmin)
