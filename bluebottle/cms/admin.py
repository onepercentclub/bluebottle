from builtins import str
from django.urls import reverse
from django.contrib import admin
from django.db import models
from django.forms import Textarea
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from fluent_contents.admin.placeholderfield import PlaceholderFieldAdmin
from parler.admin import TranslatableAdmin
from adminsortable.admin import SortableStackedInline, NonSortableParentAdmin, SortableTabularInline
from nested_inline.admin import NestedStackedInline
from solo.admin import SingletonModelAdmin

from bluebottle.statistics.statistics import Statistics

from bluebottle.cms.models import (
    SiteLinks, Link, LinkGroup, LinkPermission, SitePlatformSettings,
    Stat, Quote, Step, Logo, ResultPage, HomePage, ContentLink,
    Greeting
)
from bluebottle.utils.admin import BasePlatformSettingsAdmin
from bluebottle.utils.widgets import SecureAdminURLFieldWidget


@admin.register(LinkPermission)
class LinkPermissionAdmin(admin.ModelAdmin):
    model = LinkPermission

    def get_model_perms(self, request):
        return {}


class LinkInline(SortableStackedInline):
    model = Link
    extra = 0

    fields = (
        'title', 'link_permissions',
        'highlight', 'open_in_new_tab',
        'link'
    )


@admin.register(LinkGroup)
class LinkGroupAdmin(NonSortableParentAdmin):
    model = LinkGroup
    inlines = [LinkInline]

    def get_model_perms(self, request):
        return {}

    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse('admin:cms_sitelinks_change', args=(obj.site_links_id,)))

    def response_change(self, request, obj):
        return redirect(reverse('admin:cms_sitelinks_change', args=(obj.site_links_id,)))


class LinkGroupInline(SortableTabularInline):
    model = LinkGroup
    readonly_fields = ('title', 'edit_url',)
    fields = ('name', 'title', 'edit_url',)
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


@admin.register(SiteLinks)
class SiteLinksAdmin(NonSortableParentAdmin):
    model = SiteLinks
    inlines = [LinkGroupInline]


class StatInline(NestedStackedInline, SortableStackedInline):
    model = Stat
    extra = 0
    fields = ('type', 'definition', 'title', 'value')

    readonly_fields = ['definition']

    def definition(self, obj):
        return getattr(Statistics, obj.type).__doc__


class QuoteInline(NestedStackedInline):
    model = Quote
    extra = 1


class StepInline(NestedStackedInline, SortableStackedInline):
    model = Step
    extra = 0
    formfield_overrides = {
        models.URLField: {'widget': SecureAdminURLFieldWidget()},
    }


class LogoInline(NestedStackedInline, SortableStackedInline):
    model = Logo
    extra = 0


class ContentLinkInline(NestedStackedInline, SortableStackedInline):
    model = ContentLink
    extra = 0


class GreetingInline(NestedStackedInline):
    model = Greeting
    extra = 0


@admin.register(ResultPage)
class ResultPageAdmin(PlaceholderFieldAdmin, TranslatableAdmin, NonSortableParentAdmin):
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


@admin.register(HomePage)
class HomePageAdmin(TranslatableAdmin, SingletonModelAdmin, PlaceholderFieldAdmin, NonSortableParentAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    fields = ('content',)


@admin.register(SitePlatformSettings)
class SitePlatformSettingsAdmin(TranslatableAdmin, BasePlatformSettingsAdmin):

    fieldsets = (
        (
            _('Contact'),
            {
                'fields': (
                    'contact_email', 'contact_phone', 'start_page'
                )
            }
        ),
        (
            _('Powered by'),
            {
                'fields': (
                    'copyright', 'powered_by_text', 'powered_by_link', 'powered_by_logo', 'footer_banner'
                )
            }
        ),
        (
            _('Metadata'),
            {
                'fields': (
                    'metadata_title', 'metadata_description', 'metadata_keywords'
                )
            }
        ),
        (
            _('Styling'),
            {
                'fields': (
                    'logo', 'favicon',
                    'action_color', 'action_text_color', 'alternative_link_color',
                    'description_color', 'description_text_color',
                    'footer_color', 'footer_text_color',
                    'title_font', 'body_font'
                )
            }
        ),
    )
