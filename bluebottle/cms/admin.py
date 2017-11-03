from django.core.urlresolvers import reverse
from django.contrib import admin
from django.db import models
from django.forms import Textarea
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_singleton_admin.admin import SingletonAdmin
from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from parler.admin import TranslatableAdmin
from adminsortable.admin import SortableStackedInline, NonSortableParentAdmin, SortableTabularInline
from nested_inline.admin import NestedStackedInline

from bluebottle.statistics.statistics import Statistics

from bluebottle.cms.models import (
    SiteLinks, Link, LinkGroup, LinkPermission, SitePlatformSettings,
    Stat, Quote, Slide, Step, Logo, ContentLink, ResultPage, HomePage,
)


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


class StatInline(NestedStackedInline, SortableStackedInline):
    model = Stat
    extra = 1
    fields = ('type', 'definition', 'title', 'value')

    readonly_fields = ['definition']

    def definition(self, obj):
        return getattr(Statistics, obj.type).__doc__


class QuoteInline(NestedStackedInline):
    model = Quote
    extra = 1


class SlideInline(NestedStackedInline):
    model = Slide
    extra = 1


class StepInline(NestedStackedInline):
    model = Step
    extra = 1


class LogoInline(NestedStackedInline):
    model = Logo
    extra = 1


class LinkInline(NestedStackedInline):
    model = ContentLink
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


class HomePageAdmin(SingletonAdmin, PlaceholderFieldAdmin, TranslatableAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    fields = ('content', )


class SitePlatformSettingsAdmin(SingletonAdmin):
    pass


admin.site.register(ResultPage, ResultPageAdmin)
admin.site.register(HomePage, HomePageAdmin)
admin.site.register(SiteLinks, SiteLinksAdmin)
admin.site.register(LinkGroup, LinkGroupAdmin)
admin.site.register(LinkPermission, LinkPermissionAdmin)
admin.site.register(SitePlatformSettings, SitePlatformSettingsAdmin)
